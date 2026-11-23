import json
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import Recommendation, Assessment, Risk, AIApplication, Business
from ..config import settings

def generate_rule_based_recommendations(
    application: AIApplication,
    assessment: Optional[Assessment] = None,
    open_risks: Optional[List[Risk]] = None
) -> List[Dict[str, Any]]:
    """
    Deterministic enterprise heuristic recommendation engine.
    Maps detected gaps to high-ROI, prioritized SME interventions.
    """
    recs = []

    # 1. Fairness & Disparity Interventions
    fairness_score = assessment.fairness_score if assessment else 0.0
    has_fairness_risk = any(r.source_module == "fairness" for r in (open_risks or []))
    
    if fairness_score < 70 or has_fairness_risk:
        recs.append({
            "problem": "Demographic Disparity & Bias Exposure in Automated Decisioning",
            "why_it_matters": "Disparities in automated service quotes, package recommendations, or scheduling expose the business to consumer protection violations and brand reputational damage.",
            "action": "Implement pre-deployment fairness constraints using Fairlearn threshold optimizer, remove high-correlation proxy variables, and establish demographic disparity monitoring.",
            "priority": "High",
            "expected_business_benefit": "Shields business against regulatory audits, lowers legal risk by 80%, and prevents discriminatory customer service treatment.",
            "responsible_team": "Operations & Compliance",
            "source_module": "fairness"
        })

    # 2. Transparency & Explainability Interventions
    transparency_score = assessment.transparency_score if assessment else 0.0
    if transparency_score < 70 or application.human_oversight == "None":
        recs.append({
            "problem": "Lack of Decision Explainability & Unassisted Automated Outcomes",
            "why_it_matters": "Operating a black-box model without individual explanations or human review prevents justifiable dispute resolution and breaches emerging AI regulations.",
            "action": "Deploy local SHAP explanation cards on automated service recommendations and institute a mandatory human reviewer sign-off workflow.",
            "priority": "High",
            "expected_business_benefit": "Enables defensible audit trails, builds customer trust, and prevents catastrophic algorithmic edge-case decisions.",
            "responsible_team": "Engineering",
            "source_module": "transparency"
        })

    # 3. Privacy & Data Minimization Interventions
    privacy_score = assessment.privacy_score if assessment else 0.0
    has_privacy_risk = any(r.source_module == "privacy" for r in (open_risks or []))
    if privacy_score < 70 or has_privacy_risk:
        recs.append({
            "problem": "Unredacted PII & Loose Data Retention in Model Pipeline",
            "why_it_matters": "Ingesting and hoarding unmasked sensitive identifiers exposes the SME to severe GDPR/CCPA fines and catastrophic data breach liability.",
            "action": "Integrate automated regex PII masking at the data ingestion gateway, enforce AES-256 encryption at rest, and implement an automated 12-month data disposal schedule.",
            "priority": "High",
            "expected_business_benefit": "Minimizes cyberattack blast radius, ensures compliance with statutory privacy frameworks, and decreases cloud storage overhead.",
            "responsible_team": "Legal & Compliance",
            "source_module": "privacy"
        })

    # 4. Green AI & Carbon Footprint Interventions
    sustainability_score = assessment.sustainability_score if assessment else 0.0
    if sustainability_score < 70:
        recs.append({
            "problem": "Unmonitored Compute Energy Consumption and Carbon Emissions",
            "why_it_matters": "Unoptimized, un-quantized AI models running 24/7 in high-emission cloud regions needlessly escalate cloud bills and damage SME ESG scores.",
            "action": "Quantize inference models to INT8, enable auto-shutdown during non-working hours, and relocate persistent cloud workloads to clean-energy datacenters.",
            "priority": "Medium",
            "expected_business_benefit": "Reduces model hosting compute costs by 35-45% and cuts Scope 2/3 operational carbon footprint by up to 60%.",
            "responsible_team": "Engineering",
            "source_module": "sustainability"
        })

    # 5. Overarching Executive Governance
    overall_score = assessment.overall_score if assessment else 50.0
    if overall_score < 80:
        recs.append({
            "problem": "Absence of Formal SME Responsible AI Governance Charter",
            "why_it_matters": "Without an executive-endorsed AI ethics policy, cross-functional teams operate in silos with conflicting priorities regarding AI risk and speed-to-market.",
            "action": "Adopt the RAI-Biz SME Governance Charter, assign designated risk owners for each production AI application, and mandate quarterly self-assessments.",
            "priority": "Medium",
            "expected_business_benefit": "Establishes investor confidence, aligns engineering with risk management, and proactively prepares the enterprise for mandatory AI audits.",
            "responsible_team": "Executive Leadership",
            "source_module": "governance"
        })

    return recs

def try_llm_enhanced_recommendations(
    application: AIApplication,
    business: Business,
    assessment: Optional[Assessment],
    open_risks: List[Risk]
) -> Optional[List[Dict[str, Any]]]:
    """Attempts LLM recommendation generation if GEMINI_API_KEY is configured."""
    api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an expert Responsible AI Governance Advisor for Small and Medium Enterprises (SMEs).
Analyze this SME profile and risk findings to produce 4-5 prioritized, concrete business recommendations.

BUSINESS PROFILE:
- Business: {business.name} ({business.industry}, {business.size} employees, {business.location})
- AI System: {application.name} ({application.business_function})
- Purpose: {application.purpose}
- Decision Impact: {application.automated_decision_impact}
- Human Oversight: {application.human_oversight}

AUDIT SCORES:
- Overall: {assessment.overall_score if assessment else 'N/A'}/100
- Fairness: {assessment.fairness_score if assessment else 'N/A'}/100
- Transparency: {assessment.transparency_score if assessment else 'N/A'}/100
- Privacy: {assessment.privacy_score if assessment else 'N/A'}/100
- Sustainability: {assessment.sustainability_score if assessment else 'N/A'}/100

ACTIVE RISKS:
{chr(10).join([f"- [{r.severity}] {r.title}: {r.description} (Evidence: {r.evidence})" for r in open_risks[:5]])}

INSTRUCTIONS:
Return a valid JSON array of objects. Do NOT invent fake scores or certifications.
Each object must have exactly these keys:
- "problem": Short title of the deficiency
- "why_it_matters": Business, regulatory, or ethical risk
- "action": Concrete step the SME can execute
- "priority": "High" | "Medium" | "Low"
- "expected_business_benefit": Measurable commercial/operational upside
- "responsible_team": "Engineering" | "Legal & Compliance" | "HR & Operations" | "Executive Leadership"
- "source_module": "fairness" | "transparency" | "privacy" | "sustainability" | "governance"
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        if response.text:
            parsed = json.loads(response.text)
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
    except Exception:
        pass
    return None

def generate_and_save_recommendations(
    db: Session,
    application_id: int,
    assessment_id: Optional[int] = None
) -> List[Recommendation]:
    application = db.query(AIApplication).filter(AIApplication.id == application_id).first()
    if not application:
        raise ValueError("Application not found")

    business = db.query(Business).filter(Business.id == application.business_id).first()
    assessment = None
    if assessment_id:
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    else:
        assessment = db.query(Assessment).filter(Assessment.application_id == application_id, Assessment.is_current == True).first()

    open_risks = db.query(Risk).filter(Risk.application_id == application_id, Risk.status != "Resolved").all()

    # Try LLM first if available, otherwise use deterministic rule-based engine
    raw_recs = try_llm_enhanced_recommendations(application, business, assessment, open_risks)
    if not raw_recs:
        raw_recs = generate_rule_based_recommendations(application, assessment, open_risks)

    saved_recs = []
    # Clear existing pending recommendations to avoid duplicates
    db.query(Recommendation).filter(
        Recommendation.application_id == application_id,
        Recommendation.status == "Pending"
    ).delete()

    for r_data in raw_recs:
        rec = Recommendation(
            application_id=application_id,
            assessment_id=assessment.id if assessment else None,
            problem=r_data.get("problem", "Identified Governance Gap"),
            why_it_matters=r_data.get("why_it_matters", "Poses compliance and business exposure."),
            action=r_data.get("action", "Formulate targeted remediation plan."),
            priority=r_data.get("priority", "High"),
            expected_business_benefit=r_data.get("expected_business_benefit", "Mitigates operational and legal exposure."),
            responsible_team=r_data.get("responsible_team", "Engineering"),
            status="Pending",
            source_module=r_data.get("source_module", "assessment")
        )
        db.add(rec)
        saved_recs.append(rec)

    db.commit()
    return saved_recs
