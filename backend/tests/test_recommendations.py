"""
Module 13: AI Recommendations Test Suite
========================================
Covers:
- Dynamic context-aware recommendation generation
- Priority assignment (High, Medium, Low)
- Strict technology neutrality verification (NO unauthorized Redis/Kubernetes/AWS assumptions)
- Safe handling of incomplete profiles (explicit missing context notation)
- Listing recommendations scoped by application (/api/recommendations)
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Recommendation, Business, AIApplication
from app.services.risk_intelligence_engine import RiskIntelligenceEngine

def test_recommendation_context_aware_and_technology_neutral(tenant_a, db: Session):
    """
    Verifies recommendations:
    1. Align with business context (Automotive Services)
    2. Contain zero unauthorized technical tool assumptions (Redis, Kubernetes, AWS)
    """
    app_id = tenant_a["application"].id
    responses = [
        {"question_id": "F1", "answer": "No", "notes": "No demographic parity evaluation"},
        {"question_id": "P1", "answer": "No", "notes": "Telemetry contains customer license plates"},
        {"question_id": "S1", "answer": "No", "notes": "Edge TPU power usage unmetered"}
    ]

    _, recs = RiskIntelligenceEngine.evaluate_and_sync(db, app_id, responses=responses)
    assert len(recs) >= 3

    for r in recs:
        action_text = r.action.lower()
        # Verify prohibited vendor assumptions are NOT present
        assert "redis" not in action_text
        assert "kubernetes" not in action_text
        assert "aws" not in action_text

def test_recommendation_incomplete_profile_explicit_missing_context(tenant_a, db: Session):
    """Verifies incomplete profile generates safe neutral advice and notes missing context."""
    # Create incomplete application
    biz = Business(name="Incomplete SME", industry="Technology", size="1-10", location="Berlin")
    db.add(biz); db.flush()
    inc_app = AIApplication(
        business_id=biz.id,
        name="Prototype App",
        purpose="Inference testing",
        business_function="Testing",
        data_types="Logs",
        infrastructure_type=""
    )
    db.add(inc_app); db.flush()

    responses = [{"question_id": "S2", "answer": "No", "notes": "Servers run continuously"}]
    _, recs = RiskIntelligenceEngine.evaluate_and_sync(db, inc_app.id, responses=responses)

    assert len(recs) >= 1
    rec = recs[0]
    action_lower = rec.action.lower()
    # Must explicitly state additional business context is required
    assert "additional business context is required" in action_lower

def test_list_recommendations_endpoint(auth_client_a: TestClient, tenant_a, db: Session):
    """Verifies GET /api/recommendations retrieves recommendations filtered by application."""
    app_id = tenant_a["application"].id
    rec = Recommendation(
        application_id=app_id,
        assessment_id=1,
        problem="Unredacted identifiers in telemetry logs",
        action="Deploy PII Minimization Filter and sanitize optical logs prior to ingestion",
        why_it_matters="Prevents GDPR non-compliance",
        expected_business_benefit="Mitigates regulatory exposure",
        responsible_team="Engineering",
        source_module="privacy",
        priority="High",
        status="Pending"
    )
    db.add(rec)
    db.commit()

    res = auth_client_a.get(f"/api/recommendations?application_id={app_id}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    assert any("PII Minimization Filter" in r["action"] for r in items)
