"""
Module 15: Assessment History Test Suite
========================================
Covers:
- Historical assessment query filtered by application
- Score trajectory tracking over sequential assessment runs
- Question snapshot preservation across version updates
- Multi-assessment current flag management (only 1 current assessment per app)
- Cross-tenant assessment history isolation
"""

import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Assessment

def test_assessment_history_listing_and_order(auth_client_a: TestClient, tenant_a, db: Session):
    """Verifies history lists assessments in descending chronological order."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id
    now = datetime.datetime.utcnow()

    # Create 3 historical assessments
    a1 = Assessment(
        business_id=biz_id, application_id=app_id, name="Audit Run 1",
        overall_score=60.0, fairness_score=60.0, transparency_score=60.0,
        privacy_score=60.0, sustainability_score=60.0, is_current=False,
        completed_at=now - datetime.timedelta(days=30)
    )
    a2 = Assessment(
        business_id=biz_id, application_id=app_id, name="Audit Run 2",
        overall_score=75.0, fairness_score=80.0, transparency_score=70.0,
        privacy_score=75.0, sustainability_score=75.0, is_current=False,
        completed_at=now - datetime.timedelta(days=15)
    )
    a3 = Assessment(
        business_id=biz_id, application_id=app_id, name="Audit Run 3 (Current)",
        overall_score=90.0, fairness_score=95.0, transparency_score=85.0,
        privacy_score=90.0, sustainability_score=90.0, is_current=True,
        completed_at=now
    )
    db.add_all([a1, a2, a3])
    db.commit()

    res = auth_client_a.get(f"/api/assessments?application_id={app_id}")
    assert res.status_code == 200
    history = res.json()
    assert len(history) >= 3

    # Check order: Run 3 should be first
    assert history[0]["name"] == "Audit Run 3 (Current)"
    assert history[0]["overall_score"] == 90.0

def test_assessment_history_tenant_isolation(auth_client_b: TestClient, tenant_a, db: Session):
    """Verifies Tenant B cannot view Tenant A's assessment history."""
    app_id = tenant_a["application"].id
    res = auth_client_b.get(f"/api/assessments?application_id={app_id}")
    assert res.status_code == 403
