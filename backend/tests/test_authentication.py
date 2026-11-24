"""
Module 01: Authentication Test Suite
====================================
Covers:
- Valid OTP generation, dispatch and verification
- Invalid email format rejection
- Rate limit cooldown enforcement (60s)
- Invalid OTP code rejection
- Expired OTP rejection
- Reused OTP rejection
- Max OTP attempt limit (5 attempts)
- Session creation and cookie / Bearer token issuance
- Active session profile inspection (/api/auth/me)
- Session logout and token invalidation
- Unauthorized access rejection
"""

import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User, EmailOTP, SessionRecord
from app.services.auth_service import hash_otp, hash_token
from app.services import email_service

def test_send_otp_success(client: TestClient):
    """Verifies valid email generates and dispatches an OTP."""
    res = client.post("/api/auth/send-otp", json={"email": "auth_test_user@example.com"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "dispatched" in data["message"]
    assert len(email_service.TEST_OUTBOX) >= 1
    assert email_service.TEST_OUTBOX[-1]["to"] == "auth_test_user@example.com"

def test_send_otp_invalid_email_format(client: TestClient):
    """Verifies invalid email format is rejected with HTTP 400."""
    res = client.post("/api/auth/send-otp", json={"email": "not-an-email"})
    assert res.status_code == 400
    assert "valid email" in res.json()["detail"].lower()

def test_send_otp_cooldown_enforcement(client: TestClient):
    """Verifies requesting an OTP twice within 60 seconds returns HTTP 429."""
    res1 = client.post("/api/auth/send-otp", json={"email": "cooldown_test@example.com"})
    assert res1.status_code == 200

    res2 = client.post("/api/auth/send-otp", json={"email": "cooldown_test@example.com"})
    assert res2.status_code == 429
    detail = res2.json()["detail"]
    assert "cooldown_remaining" in detail or "wait" in str(detail).lower()

def test_verify_otp_success_creates_session(client: TestClient, db: Session):
    """Verifies correct OTP authenticates, returns user, token, and sets cookie."""
    email = "new_verify_user@example.com"
    client.post("/api/auth/send-otp", json={"email": email})
    
    otp_row = db.query(EmailOTP).filter(EmailOTP.email == email, EmailOTP.is_used == False).order_by(EmailOTP.id.desc()).first()
    assert otp_row is not None
    # Force a known OTP hash for verification
    known_otp = "849201"
    otp_row.otp_hash = hash_otp(email, known_otp)
    db.commit()

    res = client.post("/api/auth/verify-otp", json={"email": email, "otp": known_otp})
    assert res.status_code == 200
    data = res.json()
    assert data["authenticated"] is True
    assert data["user"]["email"] == email
    assert data["token"] is not None
    assert "rai_biz_session" in res.cookies

def test_verify_otp_invalid_code(client: TestClient, db: Session):
    """Verifies incorrect OTP is rejected with HTTP 400."""
    email = "wrong_code_user@example.com"
    client.post("/api/auth/send-otp", json={"email": email})
    
    res = client.post("/api/auth/verify-otp", json={"email": email, "otp": "000000"})
    assert res.status_code == 400
    assert "invalid" in res.json()["detail"].lower()

def test_verify_otp_expired_code(client: TestClient, db: Session):
    """Verifies expired OTP is rejected with HTTP 400."""
    email = "expired_code_user@example.com"
    client.post("/api/auth/send-otp", json={"email": email})
    
    otp_row = db.query(EmailOTP).filter(EmailOTP.email == email, EmailOTP.is_used == False).first()
    # Expire OTP record
    otp_row.expires_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
    db.commit()

    res = client.post("/api/auth/verify-otp", json={"email": email, "otp": "123456"})
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()

def test_verify_otp_reused_code(client: TestClient, db: Session):
    """Verifies an already used OTP cannot be verified twice."""
    email = "reused_otp_user@example.com"
    client.post("/api/auth/send-otp", json={"email": email})
    
    otp_row = db.query(EmailOTP).filter(EmailOTP.email == email, EmailOTP.is_used == False).first()
    known_otp = "654321"
    otp_row.otp_hash = hash_otp(email, known_otp)
    db.commit()

    # First verification succeeds
    res1 = client.post("/api/auth/verify-otp", json={"email": email, "otp": known_otp})
    assert res1.status_code == 200

    # Second verification fails
    res2 = client.post("/api/auth/verify-otp", json={"email": email, "otp": known_otp})
    assert res2.status_code == 400

def test_verify_otp_max_attempts_lockout(client: TestClient, db: Session):
    """Verifies exceeding 5 attempts invalidates the OTP."""
    email = "attempts_lockout@example.com"
    client.post("/api/auth/send-otp", json={"email": email})

    otp_row = db.query(EmailOTP).filter(EmailOTP.email == email, EmailOTP.is_used == False).first()
    otp_row.attempts = 5
    db.commit()

    res = client.post("/api/auth/verify-otp", json={"email": email, "otp": "123456"})
    assert res.status_code == 400
    assert "maximum" in res.json()["detail"].lower() or "exceeded" in res.json()["detail"].lower()

def test_auth_me_authenticated_vs_unauthenticated(client: TestClient, tenant_a):
    """Verifies /api/auth/me returns user profile when authenticated and False when not."""
    # Unauthenticated
    res_unauth = client.get("/api/auth/me")
    assert res_unauth.status_code == 200
    assert res_unauth.json()["authenticated"] is False

    # Authenticated via Bearer Header
    client.headers["Authorization"] = tenant_a["headers"]["Authorization"]
    res_auth = client.get("/api/auth/me")
    assert res_auth.status_code == 200
    assert res_auth.json()["authenticated"] is True
    assert res_auth.json()["user"]["email"] == tenant_a["user"].email

def test_logout_invalidates_session(client: TestClient, tenant_a, db: Session):
    """Verifies logout destroys the active session in the database."""
    client.cookies.set("rai_biz_session", tenant_a["token"])
    client.headers.update(tenant_a["headers"])

    # Confirm authenticated first
    res_before = client.get("/api/auth/me")
    assert res_before.json()["authenticated"] is True

    # Logout
    res_logout = client.post("/api/auth/logout")
    assert res_logout.status_code == 200

    # Clear client headers and check me
    client.headers.pop("Authorization", None)
    res_after = client.get("/api/auth/me")
    assert res_after.json()["authenticated"] is False

    # Verify session record marked deleted in DB
    h_token = hash_token(tenant_a["token"])
    sess_db = db.query(SessionRecord).filter(SessionRecord.session_hash == h_token).first()
    assert sess_db is None
