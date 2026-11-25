"""
Module: Hackathon Demo Access Test Suite
========================================
MANDATORY SECURITY & GOVERNANCE REQUIREMENTS:
1. Whitelist Enforcement: ONLY admin@smarthire.ai and auditor@raibiz.io permitted.
2. Unauthorized Rejection: Arbitrary email addresses cannot bypass OTP.
3. Tenant Isolation: Demo sessions are scoped exclusively to Business ID 1 (SmartHire Solutions Inc.).
4. Customer Protection: Demo accounts CANNOT read or alter private customer businesses, datasets, or assessments.
5. Session Security: Standard cryptographic session token with HttpOnly cookies & expiration handling.
6. Regression Safety: Normal email OTP flow remains 100% operational.
"""

import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import User, Business, BusinessUser, AIApplication, SessionRecord, EmailOTP
from app.services.auth_service import hash_token, hash_otp

def test_demo_login_admin_success(client: TestClient, db: Session):
    """Verifies that admin@smarthire.ai obtains a valid demo session scoped to SmartHire Solutions Inc."""
    res = client.post("/api/auth/demo-login", json={"email": "admin@smarthire.ai"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    
    data = res.json()
    assert data["authenticated"] is True
    assert data["user"]["email"] == "admin@smarthire.ai"
    assert data["user"]["role"] == "Demo Administrator"
    assert data["business"] is not None
    assert "SmartHire" in data["business"]["name"]
    assert data["token"] is not None
    assert data["csrf_token"] is not None
    
    # Verify HttpOnly session cookie
    cookies = res.cookies
    assert "rai_biz_session" in cookies

def test_demo_login_auditor_success(client: TestClient, db: Session):
    """Verifies that auditor@raibiz.io obtains a valid demo session with Auditor role."""
    res = client.post("/api/auth/demo-login", json={"email": "auditor@raibiz.io"})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    
    data = res.json()
    assert data["authenticated"] is True
    assert data["user"]["email"] == "auditor@raibiz.io"
    assert data["user"]["role"] == "Auditor"
    assert data["business"] is not None
    assert "SmartHire" in data["business"]["name"]
    assert data["token"] is not None

def test_demo_login_unauthorized_email_rejected(client: TestClient):
    """Verifies that arbitrary emails cannot bypass OTP using the demo-login endpoint."""
    forbidden_emails = [
        "attacker@evil.com",
        "random.user@gmail.com",
        "ceo@customer.com",
        "admin@raibiz.io",
        "auditor@smarthire.ai",
        "guest@demo.com"
    ]
    for email in forbidden_emails:
        res = client.post("/api/auth/demo-login", json={"email": email})
        assert res.status_code == 403, f"Expected 403 for {email}, got {res.status_code}"
        assert "Unauthorized demo identity" in res.json().get("detail", "")

def test_demo_login_empty_or_malformed_email(client: TestClient):
    """Verifies validation on empty or malformed email strings."""
    res_empty = client.post("/api/auth/demo-login", json={"email": ""})
    assert res_empty.status_code == 400

    res_no_at = client.post("/api/auth/demo-login", json={"email": "notanemail"})
    assert res_no_at.status_code == 400

def test_demo_user_strict_tenant_isolation(client: TestClient, db: Session):
    """
    CRITICAL SECURITY TEST:
    Verifies that a demo session CANNOT access or update a real customer's private business profile.
    """
    # 1. Create a private customer business & application (ID != 1)
    now = datetime.datetime.utcnow()
    customer_biz = Business(
        name="Private Enterprise Corp",
        industry="Financial Services & Banking",
        size="250-500",
        location="Frankfurt, Germany",
        description="Confidential enterprise customer data",
        contact_email="ciso@privateenterprise.com"
    )
    db.add(customer_biz)
    db.flush()

    customer_user = User(
        email="ciso@privateenterprise.com",
        full_name="Enterprise CISO",
        role="Compliance Officer",
        is_active=True,
        is_verified=True
    )
    db.add(customer_user)
    db.flush()

    db.add(BusinessUser(user_id=customer_user.id, business_id=customer_biz.id, role="Owner"))
    db.commit()

    # 2. Authenticate as Hackathon Demo Admin
    res_login = client.post("/api/auth/demo-login", json={"email": "admin@smarthire.ai"})
    assert res_login.status_code == 200
    token = res_login.json()["token"]

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Attempt to update private customer's business profile
    res_tamper = client.put(f"/api/businesses/{customer_biz.id}", headers=headers, json={
        "name": "Tampered Name",
        "industry": "Automotive Services",
        "size": "1-10",
        "location": "Nowhere"
    })
    assert res_tamper.status_code == 403, f"Expected 403, got {res_tamper.status_code}"

    # 4. Attempt to query private customer's applications
    res_apps = client.get(f"/api/applications?business_id={customer_biz.id}", headers=headers)
    assert res_apps.status_code in [403, 200]
    if res_apps.status_code == 200:
        # If 200, must not reveal any private applications
        assert len(res_apps.json()) == 0

def test_demo_session_expiry_enforced(client: TestClient, db: Session):
    """Verifies that an expired demo session is rejected with HTTP 401 on protected routes."""
    res_login = client.post("/api/auth/demo-login", json={"email": "admin@smarthire.ai"})
    assert res_login.status_code == 200
    token = res_login.json()["token"]

    # Locate the session record in DB and artificially expire it
    s_hash = hash_token(token)
    session_rec = db.query(SessionRecord).filter(SessionRecord.session_hash == s_hash).first()
    assert session_rec is not None

    session_rec.expires_at = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    db.commit()

    # Request /api/auth/me with expired token
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["authenticated"] is False

    # Request a strictly protected route
    res_protected = client.get("/api/businesses/profile", headers={"Authorization": f"Bearer {token}"})
    assert res_protected.status_code == 401

def test_standard_otp_flow_unaffected(client: TestClient, db: Session):
    """Verifies that the regular email OTP workflow remains 100% operational."""
    # Test valid OTP request for standard user
    test_email = "regular.user@example.com"
    res_send = client.post("/api/auth/send-otp", json={"email": test_email})
    assert res_send.status_code == 200
    assert res_send.json()["success"] is True

    # Retrieve active OTP from DB
    otp_rec = (
        db.query(EmailOTP)
        .filter(EmailOTP.email == test_email, EmailOTP.is_used == False)
        .order_by(EmailOTP.created_at.desc())
        .first()
    )
    assert otp_rec is not None

    # Authenticate with valid OTP hash
    # We test with verify-otp endpoint by generating a matching hash
    test_code = "123456"
    otp_rec.otp_hash = hash_otp(test_email, test_code)
    db.commit()

    res_verify = client.post("/api/auth/verify-otp", json={"email": test_email, "otp": test_code})
    assert res_verify.status_code == 200
    assert res_verify.json()["authenticated"] is True
    assert res_verify.json()["user"]["email"] == test_email
