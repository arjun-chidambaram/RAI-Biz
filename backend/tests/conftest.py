"""
RAI-Biz Pytest Configuration and Global Fixtures
=================================================
MANDATORY SAFETY RULES ENFORCED:
1. 100% Isolated Test Database: sqlite:///./rai_biz_test_suite.db
2. Production Database Preservation: SHA-256 verification of backend/rai_biz.db
3. Zero destructive operations against production data
4. Mocked email and external services (no live SMTP / third-party leaks)
"""

import os
import sys
import hashlib
import datetime
import secrets
from pathlib import Path
from typing import Generator, Dict, Any
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.database import get_db
from app.models import (
    Base, User, Business, AIApplication, BusinessUser,
    SessionRecord, EmailOTP, Assessment, AssessmentResponse,
    Dataset, DatasetRecord, Risk, Recommendation
)
from app.services import auth_service, email_service
from app.services.auth_service import hash_token, hash_otp, _RATE_LIMIT_EMAIL, _RATE_LIMIT_IP

TEST_DB_FILE = BACKEND_DIR / "rai_biz_test_suite.db"
PROD_DB_FILE = BACKEND_DIR / "rai_biz.db"

# ---------------------------------------------------------------------------
# Helper: SHA-256 calculation
# ---------------------------------------------------------------------------
def compute_sha256(filepath: Path) -> str:
    if not filepath.exists():
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

PROD_DB_INITIAL_HASH = compute_sha256(PROD_DB_FILE)

# ---------------------------------------------------------------------------
# Setup Isolated Test Engine
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE.as_posix()}"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Re-create all tables on test database
Base.metadata.drop_all(bind=test_engine)
Base.metadata.create_all(bind=test_engine)

def override_get_db() -> Generator:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# ---------------------------------------------------------------------------
# Pytest Session Teardown: Verify Production Database Integrity
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def verify_production_db_unmodified():
    """Guarantees production rai_biz.db was never touched during the test run."""
    yield
    final_hash = compute_sha256(PROD_DB_FILE)
    if PROD_DB_INITIAL_HASH != "FILE_NOT_FOUND":
        assert final_hash == PROD_DB_INITIAL_HASH, (
            f"CRITICAL SAFETY VIOLATION: Production database hash changed! "
            f"Initial: {PROD_DB_INITIAL_HASH}, Final: {final_hash}"
        )

@pytest.fixture(autouse=True)
def reset_in_memory_rate_limits():
    """Resets in-memory rate limiting structures before every single test."""
    _RATE_LIMIT_EMAIL.clear()
    _RATE_LIMIT_IP.clear()
    yield
    _RATE_LIMIT_EMAIL.clear()
    _RATE_LIMIT_IP.clear()

@pytest.fixture(autouse=True)
def mock_email_delivery(monkeypatch):
    """Mocks out external email dispatch in both email_service and auth_service."""
    def dummy_send(to_email: str, otp_code: str):
        email_service.TEST_OUTBOX.append({"to": to_email, "otp": otp_code})
        return True

    monkeypatch.setattr(email_service, "send_verification_email", dummy_send)
    monkeypatch.setattr(auth_service, "send_verification_email", dummy_send)
    yield
    email_service.TEST_OUTBOX.clear()

# ---------------------------------------------------------------------------
# Reusable Database & Client Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def db() -> Generator:
    """Provides a transactional database session against the isolated test DB."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client() -> TestClient:
    """Unauthenticated FastAPI TestClient."""
    return TestClient(app)

@pytest.fixture
def tenant_a(db) -> Dict[str, Any]:
    """
    Creates synthetic Customer A:
    - User: synth_user_a_<uid>@example.com
    - Business: 'Apex Automotive Systems' (Automotive Services)
    - Application: 'Autonomous Detailing AI'
    - Session: active bearer token
    """
    now = datetime.datetime.utcnow()
    uid = secrets.token_hex(4)
    user = User(
        email=f"synth_user_a_{uid}@example.com",
        full_name="Synth User A",
        is_verified=True,
        created_at=now
    )
    db.add(user)
    db.flush()

    biz = Business(
        name=f"Apex Automotive Systems {uid}",
        industry="Automotive Services",
        size="20-50",
        location="Munich, Germany",
        description="Automated surface analysis and detailing",
        created_at=now
    )
    db.add(biz)
    db.flush()

    bu = BusinessUser(
        business_id=biz.id,
        user_id=user.id,
        role="Owner",
        created_at=now
    )
    db.add(bu)
    db.flush()

    app_obj = AIApplication(
        business_id=biz.id,
        name="Autonomous Detailing AI",
        purpose="Computer vision paint inspection and wax dispenser",
        business_function="Surface Quality Control",
        data_types="Vehicle telemetry, optical camera scans",
        automated_decision_impact="Low",
        human_oversight="Assisted",
        affected_stakeholders="Vehicle owners and detailing technicians",
        external_services="None (Local Edge Deployment)",
        infrastructure_type="Edge TPU",
        created_at=now
    )
    db.add(app_obj)
    db.flush()

    raw_token = secrets.token_hex(32)
    session_rec = SessionRecord(
        user_id=user.id,
        session_hash=hash_token(raw_token),
        created_at=now,
        expires_at=now + datetime.timedelta(days=7)
    )
    db.add(session_rec)
    db.commit()

    return {
        "user": user,
        "business": biz,
        "application": app_obj,
        "token": raw_token,
        "headers": {"Authorization": f"Bearer {raw_token}"},
        "cookies": {"rai_biz_session": raw_token}
    }

@pytest.fixture
def tenant_b(db) -> Dict[str, Any]:
    """
    Creates synthetic Customer B (Separate Tenant for Isolation Testing):
    - User: synth_user_b_<uid>@example.com
    - Business: 'BioCare Health Labs' (Healthcare & Life Sciences)
    - Application: 'Clinical Biomarker Triage'
    - Session: active bearer token
    """
    now = datetime.datetime.utcnow()
    uid = secrets.token_hex(4)
    user = User(
        email=f"synth_user_b_{uid}@example.com",
        full_name="Synth User B",
        is_verified=True,
        created_at=now
    )
    db.add(user)
    db.flush()

    biz = Business(
        name=f"BioCare Health Labs {uid}",
        industry="Healthcare & Life Sciences",
        size="100-250",
        location="Boston, MA",
        description="Clinical diagnostic biomarkers",
        created_at=now
    )
    db.add(biz)
    db.flush()

    bu = BusinessUser(
        business_id=biz.id,
        user_id=user.id,
        role="Owner",
        created_at=now
    )
    db.add(bu)
    db.flush()

    app_obj = AIApplication(
        business_id=biz.id,
        name="Clinical Biomarker Triage",
        purpose="Patient acuity triage based on bloodwork biomarkers",
        business_function="Clinical Decision Support",
        data_types="Histopathology, EHR, patient age, diagnosis codes",
        automated_decision_impact="High",
        human_oversight="Assisted",
        affected_stakeholders="Patients and oncology clinicians",
        external_services="None (HIPAA Private Server)",
        infrastructure_type="On-Premises GPU Server",
        created_at=now
    )
    db.add(app_obj)
    db.flush()

    raw_token = secrets.token_hex(32)
    session_rec = SessionRecord(
        user_id=user.id,
        session_hash=hash_token(raw_token),
        created_at=now,
        expires_at=now + datetime.timedelta(days=7)
    )
    db.add(session_rec)
    db.commit()

    return {
        "user": user,
        "business": biz,
        "application": app_obj,
        "token": raw_token,
        "headers": {"Authorization": f"Bearer {raw_token}"},
        "cookies": {"rai_biz_session": raw_token}
    }

@pytest.fixture
def auth_client_a(client, tenant_a) -> TestClient:
    """TestClient pre-authenticated as Tenant A."""
    client.cookies.set("rai_biz_session", tenant_a["token"])
    client.headers.update(tenant_a["headers"])
    return client

@pytest.fixture
def auth_client_b(client, tenant_b) -> TestClient:
    """TestClient pre-authenticated as Tenant B."""
    client.cookies.set("rai_biz_session", tenant_b["token"])
    client.headers.update(tenant_b["headers"])
    return client
