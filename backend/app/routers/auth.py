import hmac
import secrets
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..config import settings
from ..models import User, Business
from ..schemas import (
    SendOTPRequest, VerifyOTPRequest, ResendOTPRequest,
    UserResponse, BusinessResponse, AIApplicationResponse, AuthStatusResponse
)
from ..services.auth_service import (
    request_otp, verify_otp_and_authenticate,
    validate_session, terminate_session, get_user_primary_business,
    get_user_primary_application
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def get_client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None

def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Extracts session token from HttpOnly cookie or Authorization Bearer header.
    Returns authenticated active User or None.
    """
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        # Check Authorization header (Bearer <token>)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        return None

    return validate_session(db, token)

def require_current_user(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """FastAPI dependency that enforces authentication."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with your email."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive."
        )
    return user

def verify_csrf(request: Request):
    """Verifies CSRF token for state-changing requests."""
    cookie_token = request.cookies.get(settings.CSRF_COOKIE_NAME)
    header_token = request.headers.get("X-CSRF-Token")
    if cookie_token and header_token:
        if not hmac.compare_digest(cookie_token, header_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid CSRF token."
            )

@router.post("/send-otp")
def send_otp_endpoint(
    req: SendOTPRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Requests a 6-digit OTP for email login/registration.
    Dispatches email via SMTP and sets 60-second cooldown.
    """
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")

    client_ip = get_client_ip(request)
    success, message, cooldown = request_otp(db, req.email, client_ip)

    if not success:
        if cooldown:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"message": message, "cooldown_remaining": cooldown}
            )
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "email": req.email.strip().lower()
    }

@router.post("/resend-otp")
def resend_otp_endpoint(
    req: ResendOTPRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Resends a new 6-digit OTP after 60-second cooldown."""
    if not req.email or "@" not in req.email:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")

    client_ip = get_client_ip(request)
    success, message, cooldown = request_otp(db, req.email, client_ip)

    if not success:
        if cooldown:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"message": message, "cooldown_remaining": cooldown}
            )
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "email": req.email.strip().lower()
    }

@router.post("/verify-otp", response_model=AuthStatusResponse)
def verify_otp_endpoint(
    req: VerifyOTPRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Verifies 6-digit OTP, authenticates or creates user,
    and sets HttpOnly session cookie and CSRF cookie.
    """
    client_ip = get_client_ip(request)
    success, message, user, session_token, csrf_token = verify_otp_and_authenticate(
        db, req.email, req.otp, client_ip
    )

    if not success or not user or not session_token:
        raise HTTPException(status_code=400, detail=message)

    # Secure cookie configuration
    is_prod = settings.ENVIRONMENT.lower() == "production"
    max_age_seconds = settings.SESSION_MAX_AGE_DAYS * 86400

    # Set HttpOnly Session Cookie
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_token,
        max_age=max_age_seconds,
        expires=max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=is_prod,
        path="/"
    )

    # Set readable CSRF Cookie for frontend protection
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age_seconds,
        expires=max_age_seconds,
        httponly=False,
        samesite="lax",
        secure=is_prod,
        path="/"
    )

    primary_biz = get_user_primary_business(db, user.id)
    primary_app = get_user_primary_application(db, user.id)

    return AuthStatusResponse(
        authenticated=True,
        user=UserResponse.from_orm(user),
        business=BusinessResponse.from_orm(primary_biz) if primary_biz else None,
        application=AIApplicationResponse.from_orm(primary_app) if primary_app else None,
        csrf_token=csrf_token,
        message=message
    )

@router.get("/me", response_model=AuthStatusResponse)
def get_current_user_profile(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Returns current authenticated user status, user profile,
    and active business workspace.
    """
    user = get_current_user(request, db)
    if not user:
        return AuthStatusResponse(
            authenticated=False,
            user=None,
            business=None,
            application=None,
            csrf_token=None,
            message="No active session found."
        )

    primary_biz = get_user_primary_business(db, user.id)
    primary_app = get_user_primary_application(db, user.id)
    csrf_token = request.cookies.get(settings.CSRF_COOKIE_NAME)
    if not csrf_token:
        csrf_token = secrets.token_hex(16)
        response.set_cookie(
            key=settings.CSRF_COOKIE_NAME,
            value=csrf_token,
            max_age=settings.SESSION_MAX_AGE_DAYS * 86400,
            httponly=False,
            samesite="lax",
            secure=settings.ENVIRONMENT.lower() == "production",
            path="/"
        )

    return AuthStatusResponse(
        authenticated=True,
        user=UserResponse.from_orm(user),
        business=BusinessResponse.from_orm(primary_biz) if primary_biz else None,
        application=AIApplicationResponse.from_orm(primary_app) if primary_app else None,
        csrf_token=csrf_token,
        message="Active session verified."
    )

@router.post("/logout")
def logout_endpoint(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Logs out the user, invalidates the database session record,
    and clears session cookies.
    """
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if token:
        terminate_session(db, token)

    # Delete cookies
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax"
    )
    response.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        path="/",
        httponly=False,
        samesite="lax"
    )

    return {"success": True, "message": "Successfully logged out."}
