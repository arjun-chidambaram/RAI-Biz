"""
Module 14: Reports & PDF Generation Test Suite
==============================================
Covers:
- Executive PDF governance audit report generation
- Validation of valid %PDF binary stream and content headers
- Dual-mode authentication (Bearer header + query parameter token)
- Cross-tenant PDF download prevention (HTTP 403)
- Non-existent assessment ID error handling (HTTP 404)
"""

import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Assessment

def test_generate_pdf_report_success(auth_client_a: TestClient, tenant_a, db: Session):
    """Verifies generating an executive PDF returns application/pdf with %PDF magic header."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id
    now = datetime.datetime.utcnow()

    assessment = Assessment(
        business_id=biz_id,
        application_id=app_id,
        name="Executive Audit PDF Target",
        overall_score=92.5,
        fairness_score=95.0,
        transparency_score=90.0,
        privacy_score=90.0,
        sustainability_score=95.0,
        is_current=True,
        completed_at=now
    )
    db.add(assessment)
    db.commit()

    res = auth_client_a.get(f"/api/reports/{assessment.id}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment" in res.headers["content-disposition"]
    # Check %PDF binary magic bytes
    assert res.content.startswith(b"%PDF")
    assert len(res.content) > 1000

def test_generate_pdf_with_query_token_fallback(client: TestClient, tenant_a, db: Session):
    """Verifies browser tab download via ?token=<token> fallback authenticates successfully."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id

    assessment = Assessment(
        business_id=biz_id,
        application_id=app_id,
        name="Browser Tab Query Token Target",
        overall_score=88.0,
        fairness_score=90.0,
        transparency_score=85.0,
        privacy_score=85.0,
        sustainability_score=92.0,
        is_current=True,
        completed_at=datetime.datetime.utcnow()
    )
    db.add(assessment)
    db.commit()

    # Request without headers or cookies, but with ?token=
    res = client.get(f"/api/reports/{assessment.id}?token={tenant_a['token']}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")

def test_cross_tenant_pdf_access_rejected(auth_client_b: TestClient, tenant_a, db: Session):
    """Verifies Tenant B cannot download Tenant A's private assessment report (HTTP 403)."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id

    private_assessment = Assessment(
        business_id=biz_id,
        application_id=app_id,
        name="Confidential Automotive Report",
        overall_score=75.0,
        fairness_score=80.0,
        transparency_score=70.0,
        privacy_score=70.0,
        sustainability_score=80.0,
        completed_at=datetime.datetime.utcnow()
    )
    db.add(private_assessment)
    db.commit()

    # Tenant B tries to access Tenant A's PDF
    res = auth_client_b.get(f"/api/reports/{private_assessment.id}")
    assert res.status_code == 403

def test_pdf_report_non_existent_assessment_returns_404(auth_client_a: TestClient):
    """Verifies requesting non-existent assessment returns HTTP 404."""
    res = auth_client_a.get("/api/reports/999999")
    assert res.status_code == 404
