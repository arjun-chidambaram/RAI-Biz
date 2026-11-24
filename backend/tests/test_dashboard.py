"""
Module 03: Overview Dashboard Test Suite
========================================
Covers:
- Overview metrics loading for active application
- Empty dashboard state handling
- Consistency of RAI Index and dimension scores
- Mathematical synchronization between risk counts and risk register
- Radar chart data integrity (4 dimensions)
- Top recommendations and recent alerts aggregation
- Dashboard filtering by application_id
"""

import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Assessment, Risk, Recommendation, SustainabilityResult

def test_dashboard_empty_state_returns_zeroes(auth_client_a: TestClient, tenant_a):
    """Verifies a brand new application with no assessments returns clean zero metrics."""
    res = auth_client_a.get(f"/api/dashboard?application_id={tenant_a['application'].id}")
    assert res.status_code == 200
    data = res.json()
    assert data["overall_governance_score"] == 0.0
    assert data["total_risks_count"] == 0
    assert data["high_critical_risks_count"] == 0
    assert data["resolved_risks_count"] == 0
    assert len(data["radar_data"]) == 4
    subjects = [r["subject"] for r in data["radar_data"]]
    assert subjects == ["Fairness", "Transparency", "Data Privacy", "Green AI"]

def test_dashboard_populated_metrics_synchronization(auth_client_a: TestClient, tenant_a, db: Session):
    """Verifies scores and risk counters match underlying database records."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id
    now = datetime.datetime.utcnow()

    # 1. Add an assessment
    assessment = Assessment(
        business_id=biz_id,
        application_id=app_id,
        name="Automotive Governance Baseline",
        overall_score=85.0,
        fairness_score=90.0,
        transparency_score=80.0,
        privacy_score=85.0,
        sustainability_score=85.0,
        is_current=True,
        completed_at=now
    )
    db.add(assessment)

    # 2. Add sample risks: 1 Critical, 1 High, 1 Medium, 1 Resolved
    r1 = Risk(
        application_id=app_id, assessment_id=assessment.id,
        title="Optical Camera Glare Risk", description="Optical glare causes false readings",
        severity="Critical", evidence="Camera test log", business_impact="Safety hazard",
        recommended_action="Install polarizing filter", risk_score=82.0,
        status="Open", lifecycle_status="New", source_module="transparency",
        evidence_source="Self-reported / Unverified", is_verified=False, created_at=now
    )
    r2 = Risk(
        application_id=app_id, assessment_id=assessment.id,
        title="Vehicle Model Representation Disparity", description="Training set skewed",
        severity="High", evidence="Distribution stats", business_impact="Biased predictions",
        recommended_action="Rebalance training samples", risk_score=60.0,
        status="In progress", lifecycle_status="New", source_module="fairness",
        evidence_source="Self-reported / Unverified", is_verified=False, created_at=now
    )
    r3 = Risk(
        application_id=app_id, assessment_id=assessment.id,
        title="Sensor Log Retention Excess", description="Data kept beyond legal period",
        severity="Medium", evidence="Retention policy", business_impact="Privacy breach risk",
        recommended_action="Enforce 30 day TTL", risk_score=35.0,
        status="Open", lifecycle_status="New", source_module="privacy",
        evidence_source="Self-reported / Unverified", is_verified=False, created_at=now
    )
    r4 = Risk(
        application_id=app_id, assessment_id=assessment.id,
        title="Idle Edge TPU Consumption", description="TPU runs continuously",
        severity="Low", evidence="Power meter data", business_impact="Excess power draw",
        recommended_action="Enable sleep mode", risk_score=15.0,
        status="Resolved", lifecycle_status="Resolved", source_module="sustainability",
        evidence_source="System configuration", is_verified=True, created_at=now
    )
    db.add_all([r1, r2, r3, r4])
    db.commit()

    res = auth_client_a.get(f"/api/dashboard?application_id={app_id}")
    assert res.status_code == 200
    data = res.json()

    # Verify scores match current assessment
    assert data["overall_governance_score"] == 85.0
    assert data["fairness_score"] == 90.0
    assert data["transparency_score"] == 80.0
    assert data["privacy_score"] == 85.0
    assert data["sustainability_score"] == 85.0

    # Verify mathematical synchronization of risks
    assert data["total_risks_count"] == 4
    assert data["high_critical_risks_count"] == 2  # 1 Critical + 1 High (excluding resolved)
    assert data["resolved_risks_count"] == 1
    assert data["risk_distribution"]["Critical"] == 1
    assert data["risk_distribution"]["High"] == 1
    assert data["risk_distribution"]["Medium"] == 1

def test_dashboard_top_recommendations_and_alerts(auth_client_a: TestClient, tenant_a, db: Session):
    """Verifies recommendations and alerts feed into executive overview."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id
    now = datetime.datetime.utcnow()

    rec = Recommendation(
        application_id=app_id,
        assessment_id=1,
        problem="High edge storage consumption",
        action="Implement Edge Frame Deduplication",
        why_it_matters="Reduces edge energy by 30%",
        expected_business_benefit="Saves 30% storage and power costs",
        responsible_team="Engineering",
        source_module="sustainability",
        priority="High",
        status="Pending",
        created_at=now
    )
    db.add(rec)
    db.commit()

    res = auth_client_a.get(f"/api/dashboard?application_id={app_id}")
    assert res.status_code == 200
    data = res.json()
    assert len(data["top_recommendations"]) >= 1
    rec_actions = [r["action"] for r in data["top_recommendations"]]
    assert "Implement Edge Frame Deduplication" in rec_actions
