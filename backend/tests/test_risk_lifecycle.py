"""
Module 12: Risk Lifecycle Management Test Suite
===============================================
Covers:
- Full lifecycle status transitions:
  1. Open / New -> In progress (with assigned owner and target date)
  2. In progress -> Resolved (with completion notes)
  3. Resolved -> Reopened (regression detected on subsequent assessment)
- Immutable remediation history JSON audit logging
- Verification flag and evidence source escalation
- PATCH /api/risks/{id} endpoint validation
"""

import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Risk
from app.services.risk_intelligence_engine import RiskIntelligenceEngine

def test_risk_lifecycle_transitions_and_audit_history(auth_client_a: TestClient, tenant_a, db: Session):
    """Verifies complete state machine transitions and audit trail persistence."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id

    # 1. Create a baseline risk
    r = Risk(
        application_id=app_id,
        title="Unencrypted Telemetry Cache",
        description="Local telemetry cache is stored without encryption",
        severity="High",
        evidence="Observed plaintext sqlite db on device",
        business_impact="Physical device access allows telemetry extraction",
        recommended_action="Enable SQLCipher or filesystem encryption",
        risk_score=65.0,
        status="Open",
        lifecycle_status="New",
        source_module="privacy",
        evidence_source="Self-reported / Unverified",
        is_verified=False
    )
    db.add(r)
    db.commit()
    risk_id = r.id

    # 2. Transition to In progress with owner and target date
    patch_1 = {
        "status": "In progress",
        "responsible_owner": "Hans Bauer (Lead Security Engineer)",
        "target_date": "2027-04-15",
        "completion_notes": "Implemented AES-256 local disk encryption for edge cache."
    }
    res_1 = auth_client_a.patch(f"/api/risks/{risk_id}", json=patch_1)
    assert res_1.status_code == 200
    updated_1 = res_1.json()
    assert updated_1["status"] == "In progress"
    assert updated_1["responsible_owner"] == "Hans Bauer (Lead Security Engineer)"
    assert updated_1["target_date"] == "2027-04-15"

    # 3. Transition to Resolved with verification
    patch_2 = {
        "status": "Resolved",
        "is_verified": True,
        "completion_notes": "Security auditor verified encryption keys deployed."
    }
    res_2 = auth_client_a.patch(f"/api/risks/{risk_id}", json=patch_2)
    assert res_2.status_code == 200
    updated_2 = res_2.json()
    assert updated_2["status"] == "Resolved"
    assert updated_2["is_verified"] is True

    # 4. Inspect audit history stored in database
    db.expire_all()
    db_risk = db.query(Risk).filter(Risk.id == risk_id).first()
    history = json.loads(db_risk.remediation_history_json or "[]")
    assert len(history) >= 2
    # Verify events contain status change logs
    event_changes = [h.get("changes", "") for h in history]
    assert any("In progress" in str(c) for c in event_changes)
    assert any("Resolved" in str(c) for c in event_changes)

def test_risk_regression_reopens_resolved_risk(tenant_a, db: Session):
    """Verifies that if a compliant rule fails in a later assessment, lifecycle becomes 'Reopened'."""
    app_id = tenant_a["application"].id

    # First run: Deficient -> New
    resps_fail = [{"question_id": "F1", "answer": "No", "notes": "Disparity found"}]
    risks_1, _ = RiskIntelligenceEngine.evaluate_and_sync(db, app_id, responses=resps_fail)
    target_risk = risks_1[0]
    assert target_risk.status == "Open"

    # Second run: Compliant -> Resolved
    resps_pass = [{"question_id": "F1", "answer": "Yes", "notes": "Parity confirmed"}]
    RiskIntelligenceEngine.evaluate_and_sync(db, app_id, responses=resps_pass)
    db.refresh(target_risk)
    assert target_risk.status == "Resolved"

    # Third run: Regression -> Reopened
    RiskIntelligenceEngine.evaluate_and_sync(db, app_id, responses=resps_fail)
    db.refresh(target_risk)
    assert target_risk.status == "Open"
    assert target_risk.lifecycle_status == "Reopened"
