import json
import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import Risk
from ..schemas import RiskCreate, RiskUpdate
from .risk_intelligence_engine import RiskIntelligenceEngine

def get_risks(
    db: Session,
    application_id: Optional[int] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    source_module: Optional[str] = None
) -> List[Risk]:
    query = db.query(Risk)
    if application_id:
        query = query.filter(Risk.application_id == application_id)
    if severity:
        query = query.filter(Risk.severity == severity)
    if status:
        query = query.filter(Risk.status == status)
    if source_module:
        query = query.filter(Risk.source_module == source_module)
    return query.order_by(
        Risk.status.asc(),
        Risk.risk_score.desc(),
        Risk.created_at.desc()
    ).all()

def create_risk(db: Session, risk_in: RiskCreate, actor_email: Optional[str] = None) -> Risk:
    now = datetime.datetime.utcnow()
    initial_hist = [{
        "timestamp": now.isoformat(),
        "action": "Created",
        "status": risk_in.status,
        "severity": risk_in.severity,
        "user": actor_email or "manual_entry",
        "notes": "Created via Risk Center interface"
    }]

    risk = Risk(
        application_id=risk_in.application_id,
        assessment_id=risk_in.assessment_id,
        title=risk_in.title,
        description=risk_in.description,
        source_module=risk_in.source_module,
        severity=risk_in.severity,
        evidence=risk_in.evidence,
        business_impact=risk_in.business_impact,
        recommended_action=risk_in.recommended_action,
        status=risk_in.status,
        risk_key=risk_in.risk_key or risk_in.title[:50],
        category=risk_in.category or risk_in.source_module,
        likelihood=risk_in.likelihood or "Medium",
        impact=risk_in.impact or "Medium",
        exposure_factor=risk_in.exposure_factor or "Medium",
        control_effectiveness=risk_in.control_effectiveness or "Weak",
        risk_score=risk_in.risk_score or 50.0,
        evidence_source=risk_in.evidence_source or "Manual entry",
        is_verified=risk_in.is_verified or False,
        lifecycle_status=risk_in.lifecycle_status or "New",
        responsible_owner=risk_in.responsible_owner,
        target_date=risk_in.target_date,
        completion_notes=risk_in.completion_notes,
        supporting_evidence=risk_in.supporting_evidence,
        remediation_history_json=json.dumps(initial_hist),
        created_at=now,
        updated_at=now
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk

def update_risk(db: Session, risk_id: int, risk_update: RiskUpdate, actor_email: Optional[str] = None) -> Risk:
    return RiskIntelligenceEngine.update_remediation_status(
        db=db,
        risk_id=risk_id,
        status=risk_update.status,
        severity=risk_update.severity,
        recommended_action=risk_update.recommended_action,
        responsible_owner=risk_update.responsible_owner,
        target_date=risk_update.target_date,
        completion_notes=risk_update.completion_notes,
        supporting_evidence=risk_update.supporting_evidence,
        is_verified=risk_update.is_verified,
        actor_email=actor_email
    )
