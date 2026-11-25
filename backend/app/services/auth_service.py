import hmac
import hashlib
import secrets
import datetime
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from ..models import User, EmailOTP, SessionRecord, Business, BusinessUser, AIApplication
from ..config import settings
from .email_service import send_verification_email

# In-memory rate limiting structures
# Structure: { key: [timestamps] }
_RATE_LIMIT_EMAIL: Dict[str, List[datetime.datetime]] = {}
_RATE_LIMIT_IP: Dict[str, List[datetime.datetime]] = {}

OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60
RATE_LIMIT_WINDOW_MINUTES = 10
MAX_REQUESTS_PER_WINDOW = 5

def _clean_rate_limit_window(records: Dict[str, List[datetime.datetime]], key: str, window_minutes: int):
    now = datetime.datetime.utcnow()
    cutoff = now - datetime.timedelta(minutes=window_minutes)
    if key in records:
        records[key] = [ts for ts in records[key] if ts > cutoff]
        if not records[key]:
            del records[key]

def check_rate_limit(key: str, records: Dict[str, List[datetime.datetime]], max_requests: int = MAX_REQUESTS_PER_WINDOW) -> bool:
    """Returns True if request is allowed, False if rate-limited."""
    _clean_rate_limit_window(records, key, RATE_LIMIT_WINDOW_MINUTES)
    timestamps = records.get(key, [])
    if len(timestamps) >= max_requests:
        return False
    timestamps.append(datetime.datetime.utcnow())
    records[key] = timestamps
    return True

def generate_secure_otp() -> str:
    """Generates a cryptographically secure 6-digit numeric OTP."""
    code_int = secrets.randbelow(1_000_000)
    return f"{code_int:06d}"

def hash_otp(email: str, otp: str) -> str:
    """Computes SHA-256 hash of email, OTP, and application secret salt."""
    normalized_email = email.strip().lower()
    payload = f"{normalized_email}:{otp.strip()}:{settings.SECRET_KEY}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def hash_token(token: str) -> str:
    """Computes SHA-256 hash of session token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def request_otp(db: Session, email: str, client_ip: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
    """
    Validates email, checks cooldown & rate limits, generates secure OTP,
    hashes & persists it, and dispatches verification email.
    Returns: (success: bool, message: str, cooldown_remaining: Optional[int])
    """
    normalized_email = email.strip().lower()
    
    # 1. IP rate limiting
    if client_ip and not check_rate_limit(client_ip, _RATE_LIMIT_IP, max_requests=10):
        return False, "Too many requests from this network. Please try again later.", None

    # 2. Email rate limiting
    if not check_rate_limit(normalized_email, _RATE_LIMIT_EMAIL, max_requests=MAX_REQUESTS_PER_WINDOW):
        return False, "Too many OTP requests for this email address. Please try again later.", None

    # 3. 60-second cooldown check from latest active OTP
    now = datetime.datetime.utcnow()
    latest_otp = (
        db.query(EmailOTP)
        .filter(EmailOTP.email == normalized_email, EmailOTP.is_used == False)
        .order_by(EmailOTP.created_at.desc())
        .first()
    )

    if latest_otp:
        elapsed_seconds = (now - latest_otp.created_at).total_seconds()
        if elapsed_seconds < RESEND_COOLDOWN_SECONDS:
            remaining = int(RESEND_COOLDOWN_SECONDS - elapsed_seconds)
            return False, f"Please wait {remaining} seconds before requesting a new code.", remaining

    # 4. Generate secure 6-digit OTP & expiration
    otp_code = generate_secure_otp()
    otp_hash = hash_otp(normalized_email, otp_code)
    expires_at = now + datetime.timedelta(minutes=OTP_EXPIRY_MINUTES)

    # 5. Dispatch verification email BEFORE committing to database
    # Critical: Do not show success or start cooldown unless SMTP server accepts the message
    try:
        send_verification_email(normalized_email, otp_code)
    except Exception as e:
        # Rollback rate limit addition if email failed
        if client_ip and client_ip in _RATE_LIMIT_IP and _RATE_LIMIT_IP[client_ip]:
            _RATE_LIMIT_IP[client_ip].pop()
        if normalized_email in _RATE_LIMIT_EMAIL and _RATE_LIMIT_EMAIL[normalized_email]:
            _RATE_LIMIT_EMAIL[normalized_email].pop()
        return False, f"Email delivery failed: {str(e)}", None

    # 6. Invalidate all previous active OTPs for this email only after delivery succeeds
    db.query(EmailOTP).filter(
        EmailOTP.email == normalized_email,
        EmailOTP.is_used == False
    ).update({"is_used": True})

    # 7. Persist verified active OTP in database
    otp_record = EmailOTP(
        email=normalized_email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0,
        is_used=False,
        created_at=now
    )
    db.add(otp_record)
    db.commit()

    return True, f"A 6-digit verification code has been dispatched to {normalized_email}.", None

def verify_otp_and_authenticate(
    db: Session,
    email: str,
    otp: str,
    client_ip: Optional[str] = None
) -> Tuple[bool, str, Optional[User], Optional[str], Optional[str]]:
    """
    Verifies 6-digit OTP:
    - Checks expiration (5 min)
    - Checks max attempts (5)
    - Compares hashes securely
    - Creates or authenticates User
    - Associates with Business
    - Creates server session and returns (success, message, user, session_token, csrf_token)
    """
    normalized_email = email.strip().lower()
    now = datetime.datetime.utcnow()

    # Look up latest unused OTP
    otp_record = (
        db.query(EmailOTP)
        .filter(EmailOTP.email == normalized_email, EmailOTP.is_used == False)
        .order_by(EmailOTP.created_at.desc())
        .first()
    )

    if not otp_record:
        return False, "No active verification code found. Please request a new code.", None, None, None

    # Check expiration
    if now > otp_record.expires_at:
        otp_record.is_used = True
        db.commit()
        return False, "Verification code has expired. Please request a new code.", None, None, None

    # Check max attempts
    if otp_record.attempts >= MAX_OTP_ATTEMPTS:
        otp_record.is_used = True
        db.commit()
        return False, "Maximum verification attempts exceeded. Please request a new code.", None, None, None

    # Increment attempts count
    otp_record.attempts += 1
    db.commit()

    # Verify OTP hash using constant-time comparison
    expected_hash = hash_otp(normalized_email, otp)
    if not hmac.compare_digest(otp_record.otp_hash, expected_hash):
        remaining_attempts = MAX_OTP_ATTEMPTS - otp_record.attempts
        if remaining_attempts <= 0:
            otp_record.is_used = True
            db.commit()
            return False, "Maximum verification attempts exceeded. Please request a new code.", None, None, None
        return False, f"Invalid verification code. {remaining_attempts} attempt(s) remaining.", None, None, None

    # Mark OTP as successfully used
    otp_record.is_used = True
    db.commit()

    # Get or create User
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        user = User(
            email=normalized_email,
            full_name=normalized_email.split("@")[0].replace(".", " ").title(),
            role="Compliance Officer",
            is_active=True,
            is_verified=True,
            created_at=now,
            last_login=now
        )
        db.add(user)
        db.flush()
    else:
        user.is_verified = True
        user.last_login = now
        db.commit()

    # Ensure user has a business associated in business_users
    membership = db.query(BusinessUser).filter(BusinessUser.user_id == user.id).first()
    if not membership:
        # Create a dedicated SME business for the newly registered user
        biz_name = f"{user.full_name or 'My'}'s Enterprise"
        biz = Business(
            name=biz_name,
            industry="Technology & Services",
            size="11-50",
            location="United States",
            description=f"Operational governance workspace for {normalized_email}",
            contact_email=normalized_email
        )
        db.add(biz)
        db.flush()

        # Add initial AI application
        app = AIApplication(
            business_id=biz.id,
            name="Production AI System",
            purpose="Automated decision scoring and customer service recommendation pipeline.",
            business_function="Business Operations",
            data_types="Customer Inquiries, Service Records, Operational Metrics",
            automated_decision_impact="High",
            human_oversight="Partial",
            model_type="Classification & Ranking",
            status="Active"
        )
        db.add(app)
        db.flush()

        membership = BusinessUser(
            user_id=user.id,
            business_id=biz.id,
            role="Owner"
        )
        db.add(membership)
        db.commit()

    # Create server-managed session
    session_token = secrets.token_urlsafe(32)
    session_hash = hash_token(session_token)
    session_expires = now + datetime.timedelta(days=settings.SESSION_MAX_AGE_DAYS)

    session_record = SessionRecord(
        user_id=user.id,
        session_hash=session_hash,
        expires_at=session_expires,
        created_at=now
    )
    db.add(session_record)

    csrf_token = secrets.token_hex(16)
    db.commit()

    return True, "Authentication successful", user, session_token, csrf_token

def validate_session(db: Session, session_token: Optional[str]) -> Optional[User]:
    """Validates session token and returns active User if valid and not expired."""
    if not session_token:
        return None

    s_hash = hash_token(session_token)
    now = datetime.datetime.utcnow()

    session_record = (
        db.query(SessionRecord)
        .filter(SessionRecord.session_hash == s_hash)
        .first()
    )

    if not session_record:
        return None

    if now > session_record.expires_at:
        db.delete(session_record)
        db.commit()
        return None

    user = db.query(User).filter(User.id == session_record.user_id, User.is_active == True).first()
    return user

def terminate_session(db: Session, session_token: Optional[str]):
    """Invalidates session record on logout."""
    if not session_token:
        return
    s_hash = hash_token(session_token)
    db.query(SessionRecord).filter(SessionRecord.session_hash == s_hash).delete()
    db.commit()

HACKATHON_DEMO_ACCOUNTS: Dict[str, Dict[str, str]] = {
    "admin@smarthire.ai": {
        "full_name": "SmartHire Demo Administrator",
        "user_role": "Demo Administrator",
        "biz_role": "Owner",
        "description": "Full SME executive & governance demonstration role"
    },
    "auditor@raibiz.io": {
        "full_name": "RAI-Biz Independent Auditor",
        "user_role": "Auditor",
        "biz_role": "Auditor",
        "description": "Independent auditor review & compliance verification role"
    }
}

def get_user_primary_business(db: Session, user_id: int) -> Optional[Business]:
    """Returns the most recently created or updated primary business associated with a user."""
    # Check if user is an official hackathon demo account
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.email in HACKATHON_DEMO_ACCOUNTS:
        demo_biz = db.query(Business).filter(Business.name.ilike("%SmartHire%")).first()
        if not demo_biz:
            from .demo_seed_service import seed_demo_data
            seed_res = seed_demo_data(db)
            demo_biz = db.query(Business).filter(Business.id == seed_res["business_id"]).first()
        if demo_biz:
            return demo_biz

    # First search for private businesses (id != 1) to avoid falling back to demo
    membership = (
        db.query(BusinessUser)
        .filter(BusinessUser.user_id == user_id, BusinessUser.business_id != 1)
        .order_by(BusinessUser.id.desc())
        .first()
    )
    if not membership:
        membership = (
            db.query(BusinessUser)
            .filter(BusinessUser.user_id == user_id)
            .order_by(BusinessUser.id.desc())
            .first()
        )
    if membership:
        return db.query(Business).filter(Business.id == membership.business_id).first()
    return None

def get_user_primary_application(db: Session, user_id: int) -> Optional[AIApplication]:
    """Returns the primary active AI application for the user's active business."""
    biz = get_user_primary_business(db, user_id)
    if biz:
        return db.query(AIApplication).filter(AIApplication.business_id == biz.id).order_by(AIApplication.id.desc()).first()
    return None

def authenticate_demo_account(
    db: Session,
    email: str,
    client_ip: Optional[str] = None
) -> Tuple[bool, str, Optional[User], Optional[str], Optional[str]]:
    """
    Controlled Hackathon Demo Authenticator.
    STRICT SECURITY CONTROLS:
    1. Validates requested identity strictly against HACKATHON_DEMO_ACCOUNTS whitelist.
    2. Any non-whitelisted email is rejected immediately with 403.
    3. Scopes user strictly to the SmartHire Solutions demo workspace (Business ID 1).
    4. Removes any unauthorized cross-tenant memberships.
    5. Issues a standard cryptographically signed server session record.
    Returns: (success: bool, message: str, user: Optional[User], session_token: Optional[str], csrf_token: Optional[str])
    """
    normalized_email = email.strip().lower()
    if normalized_email not in HACKATHON_DEMO_ACCOUNTS:
        return False, "Unauthorized demo identity. Demo access is strictly restricted to official hackathon demonstration accounts.", None, None, None

    demo_cfg = HACKATHON_DEMO_ACCOUNTS[normalized_email]
    now = datetime.datetime.utcnow()

    # 1. Locate or seed SmartHire Demo Business
    demo_biz = db.query(Business).filter(Business.name.ilike("%SmartHire%")).first()
    if not demo_biz:
        from .demo_seed_service import seed_demo_data
        seed_res = seed_demo_data(db)
        demo_biz = db.query(Business).filter(Business.id == seed_res["business_id"]).first()

    if not demo_biz:
        return False, "Demo workspace initialization failed.", None, None, None

    # 2. Look up or create User
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        user = User(
            email=normalized_email,
            full_name=demo_cfg["full_name"],
            role=demo_cfg["user_role"],
            is_active=True,
            is_verified=True,
            created_at=now,
            last_login=now
        )
        db.add(user)
        db.flush()
    else:
        user.full_name = demo_cfg["full_name"]
        user.role = demo_cfg["user_role"]
        user.is_active = True
        user.is_verified = True
        user.last_login = now
        db.commit()

    # 3. Ensure user's business membership is strictly scoped to the demo business
    # Remove any foreign memberships to guarantee strict tenant isolation
    db.query(BusinessUser).filter(
        BusinessUser.user_id == user.id,
        BusinessUser.business_id != demo_biz.id
    ).delete(synchronize_session=False)

    membership = db.query(BusinessUser).filter(
        BusinessUser.user_id == user.id,
        BusinessUser.business_id == demo_biz.id
    ).first()
    if not membership:
        membership = BusinessUser(
            user_id=user.id,
            business_id=demo_biz.id,
            role=demo_cfg["biz_role"]
        )
        db.add(membership)
        db.commit()
    else:
        if membership.role != demo_cfg["biz_role"]:
            membership.role = demo_cfg["biz_role"]
            db.commit()

    # 4. Create cryptographically secure server session
    session_token = secrets.token_urlsafe(32)
    session_hash = hash_token(session_token)
    session_expires = now + datetime.timedelta(days=settings.SESSION_MAX_AGE_DAYS)

    session_record = SessionRecord(
        user_id=user.id,
        session_hash=session_hash,
        expires_at=session_expires,
        created_at=now
    )
    db.add(session_record)
    csrf_token = secrets.token_hex(16)
    db.commit()

    return True, f"Hackathon demo access granted ({demo_cfg['user_role']})", user, session_token, csrf_token
