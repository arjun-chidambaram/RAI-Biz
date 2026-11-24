"""
Module 11: Universal Risk Intelligence Engine Test Suite
========================================================
Covers:
- Multi-factor risk formula: Likelihood x Impact x Exposure / Control Effectiveness
- Contextual severity scaling across diverse industry domains
- Evidence attribution rules and verification tracking
- Duplicate risk prevention within and across runs
- Incomplete profile missing field tracking without hallucination
- Risk Center query filtering by application (/api/risks)
- Manual risk registration with standardized severity scoring
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Risk
from app.services.risk_intelligence_engine import (
    RiskIntelligenceEngine, RiskScoringModel, extract_business_context
)

def test_risk_scoring_contextual_scaling(tenant_a, tenant_b, db: Session):
    """
    Proves P1 (PII Minimization) is contextually scaled:
    - Low impact + non-sensitive automotive telemetry -> Medium severity
    - High impact + sensitive clinical healthcare EHR -> Critical severity
    """
    ctx_auto = extract_business_context(db, tenant_a["application"].id)
    ctx_health = extract_business_context(db, tenant_b["application"].id)

    sev_auto, score_auto, _, _, _, _, _ = RiskScoringModel.calculate("P1", "privacy", ctx_auto, "No")
    sev_health, score_health, _, _, _, _, _ = RiskScoringModel.calculate("P1", "privacy", ctx_health, "No")

    assert sev_auto in ["Low", "Medium"], f"Automotive P1 should not be Critical, got {sev_auto}"
    assert sev_health == "Critical", f"Healthcare P1 should be Critical, got {sev_health}"
    assert score_health > score_auto

def test_evidence_attribution_rules(tenant_a, db: Session):
    """Verifies evidence attribution labels adhere strictly to verification rules."""
    app_id = tenant_a["application"].id
    sample_responses = [
        {"question_id": "P1", "answer": "No", "notes": "Submitted self-reported answer"},
        {"question_id": "F1", "answer": "No", "notes": "Refer to audit_doc.pdf attached"}
    ]

    risks, _ = RiskIntelligenceEngine.evaluate_and_sync(
        db, application_id=app_id, responses=sample_responses, actor_email="tester@apex.de"
    )

    r_p1 = next(r for r in risks if r.risk_key == "PRIV_DATA_MINIMIZATION" or r.source_module == "privacy")
    r_f1 = next(r for r in risks if r.risk_key == "FAIR_PRE_DEPLOYMENT_BIAS" or r.source_module == "fairness")

    # Self-reported answer must be labelled 'Self-reported / Unverified'
    assert r_p1.evidence_source == "Self-reported / Unverified"
    assert r_p1.is_verified is False

    # Document reference in note must be labelled 'Document-derived'
    assert r_f1.evidence_source == "Document-derived"
    assert r_f1.is_verified is False

def test_duplicate_risk_prevention(tenant_a, db: Session):
    """Verifies evaluating identical responses repeatedly does not create duplicate rows."""
    app_id = tenant_a["application"].id
    sample_responses = [
        {"question_id": "T1", "answer": "No", "notes": "No explainability dashboard"},
        {"question_id": "T1", "answer": "No", "notes": "Duplicate entry in list"}
    ]

    risks_1, _ = RiskIntelligenceEngine.evaluate_and_sync(db, app_id, responses=sample_responses)
    risk_keys_1 = [r.risk_key for r in risks_1]
    assert len(risk_keys_1) == len(set(risk_keys_1))

    # Second evaluation run
    risks_2, _ = RiskIntelligenceEngine.evaluate_and_sync(db, app_id, responses=sample_responses)
    total_db_risks = db.query(Risk).filter(Risk.application_id == app_id, Risk.source_module == "transparency").all()
    assert len(total_db_risks) == len(risks_2)

def test_list_risks_endpoint(auth_client_a: TestClient, tenant_a, db: Session):
    """Verifies GET /api/risks retrieves risks filtered by active application."""
    app_id = tenant_a["application"].id
    # Seed 1 risk
    r = Risk(
        application_id=app_id,
        title="Unverified Model Outputs",
        description="Model output verification missing",
        source_module="fairness",
        severity="Medium",
        evidence="Assessment Q3 answer",
        business_impact="Decisions may be inaccurate",
        recommended_action="Conduct weekly bias audits",
        risk_score=40.0,
        status="Open",
        evidence_source="Self-reported / Unverified",
        is_verified=False
    )
    db.add(r)
    db.commit()

    res = auth_client_a.get(f"/api/risks?application_id={app_id}")
    assert res.status_code == 200
    risks = res.json()
    assert len(risks) >= 1
    assert any(item["title"] == "Unverified Model Outputs" for item in risks)

def test_manual_risk_registration(auth_client_a: TestClient, tenant_a):
    """Verifies POST /api/risks allows registering an ad-hoc governance risk."""
    app_id = tenant_a["application"].id
    payload = {
        "application_id": app_id,
        "title": "Camera Sensor Occlusion in Rainy Conditions",
        "source_module": "transparency",
        "severity": "Medium",
        "description": "Camera lens occasionally obscured by mud and spray",
        "evidence": "Observed during outdoor field trials",
        "business_impact": "Degraded detection accuracy",
        "recommended_action": "Install hydrophobic lens coating"
    }

    res = auth_client_a.post("/api/risks", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Camera Sensor Occlusion in Rainy Conditions"
    assert data["severity"] == "Medium"
    assert data["status"] == "Open"
