"""
RAI-Biz Centralized Universal Risk Intelligence Engine
=====================================================
A business-agnostic, multi-tenant risk governance engine that automatically
assesses, scores, contextualizes, and tracks AI risks for every registered SME.

Core Principles:
1. Universal Business Support: Zero hardcoded business names or company-specific hacks.
2. Dynamic Business Context: Rigorously extracts context; missing fields are marked
   "Unknown" or "Not Provided" without hallucination.
3. Proportional Dynamic Scoring: Likelihood x Impact x Exposure / Control Effectiveness.
   Question IDs (P1, F1, T1, S1) influence risk identification dynamically based on
   data sensitivity and decision impact. No question is blindly assigned "Critical".
4. Evidence Accuracy: Clear, uncontradictory labels:
   - "Self-reported / Unverified"
   - "Document-derived" (until validated)
   - "Dataset analysis" (identifies specific dataset and scan metrics)
   - "System configuration" (telemetry metrics)
   - "Verified" (only after formal audit sign-off)
5. Context-Aware Recommendations: Solves the exact finding without unsupported vendor
   assumptions (never hallucinating Redis, AWS, K8s, etc.). Explicitly flags missing context.
6. Multi-View Synchronization: Identical records and matching counts across Top Navbar,
   Summary Cards (Critical, High, Medium, Low, In Progress, Resolved), Risk Center,
   Dashboard, Reports, and History.
7. Remediation Lifecycle: Open -> In progress -> Resolved (and Reopened upon regression).
8. Multi-Tenant Isolation: Strictly scoped by business_id and application_id.
"""

import json
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from ..models import (
    Business, AIApplication, Assessment, AssessmentResponse,
    Risk, Recommendation, FairnessResult, PrivacyFinding, SustainabilityResult, Dataset
)

# ---------------------------------------------------------------------------
# 1. DYNAMIC BUSINESS CONTEXT
# ---------------------------------------------------------------------------

@dataclass
class BusinessContext:
    business_id: int
    business_name: str
    industry: str
    size: str
    location: str
    application_id: int
    application_name: str
    purpose: str
    business_function: str
    data_types: str
    automated_decision_impact: str
    human_oversight: str
    model_type: str
    affected_stakeholders: str
    external_services: str
    infrastructure_type: str
    missing_fields: List[str] = field(default_factory=list)
    has_fairness_scan: bool = False
    has_privacy_scan: bool = False
    has_sustainability_scan: bool = False
    fairness_details: Optional[Dict[str, Any]] = None
    privacy_details: Optional[Dict[str, Any]] = None
    sustainability_details: Optional[Dict[str, Any]] = None

    @property
    def is_high_impact(self) -> bool:
        return (self.automated_decision_impact or "").strip().lower() in ["high", "critical", "irreversible"]

    @property
    def is_unassisted(self) -> bool:
        return (self.human_oversight or "").strip().lower() in ["none", "unassisted", "autonomous", "fully automated"]

    @property
    def known_infrastructure(self) -> Optional[str]:
        infra = (self.infrastructure_type or "").strip()
        if infra.lower() in ["unknown", "not provided", ""]:
            return None
        return infra

    @property
    def has_sensitive_data(self) -> bool:
        dt = (self.data_types or "").lower()
        sensitive_keywords = [
            "health", "medical", "patient", "biometric", "financial", "credit", "bank",
            "ssn", "national id", "personal", "pii", "minor", "children", "candidate",
            "applicant", "salary", "criminal", "ethnicity", "religion",
            "phone", "email", "address", "date of birth", "dob", "passport",
            "tax id", "license plate", "registration", "vehicle identifier",
            "customer contact", "contact details"
        ]
        return any(k in dt for k in sensitive_keywords)

    @property
    def has_non_sensitive_data_only(self) -> bool:
        dt = (self.data_types or "").lower()
        if self.has_sensitive_data:
            return False
        operational_keywords = [
            "vehicle", "car", "sensor", "telemetry", "machine", "hardware", "public",
            "catalog", "inventory", "code", "benchmarks", "synthetic", "weather",
            "equipment", "maintenance", "parts"
        ]
        return any(k in dt for k in operational_keywords)

    @property
    def stakeholder_description(self) -> str:
        if self.affected_stakeholders and self.affected_stakeholders not in ["Not Provided", "Unknown"]:
            return self.affected_stakeholders
        fn = (self.business_function or "").lower()
        if "customer" in fn or "client" in fn:
            return "customers and service users"
        elif "patient" in fn or "clinical" in fn or "health" in fn:
            return "patients and healthcare users"
        elif "student" in fn or "education" in fn:
            return "students and academic stakeholders"
        elif "employee" in fn or "candidate" in fn or "hiring" in fn or "recruitment" in fn:
            return "job applicants and employees"
        elif "credit" in fn or "loan" in fn or "financial" in fn:
            return "borrowers and financial consumers"
        elif "vehicle" in fn or "automotive" in fn or "car" in fn:
            return "vehicle owners and service technicians"
        return "affected end-users and impacted individuals"


def extract_business_context(db: Session, application_id: int, business_id: Optional[int] = None) -> BusinessContext:
    """
    Rigorously retrieves business profile and application context.
    If any field is missing or empty, sets it as 'Unknown' or 'Not Provided'
    and records it in missing_fields. Never invents facts.
    """
    app = db.query(AIApplication).filter(AIApplication.id == application_id).first()
    if not app:
        raise ValueError(f"AI Application ID {application_id} not found.")

    biz_id = business_id or app.business_id
    biz = db.query(Business).filter(Business.id == biz_id).first()

    missing = []

    # Business metadata
    biz_name = (biz.name or "").strip() if biz else ""
    if not biz_name:
        biz_name = "Enterprise"
        missing.append("business_name")

    industry = (biz.industry or "").strip() if biz else ""
    if not industry or industry.lower() in ["unknown", "n/a"]:
        industry = "Unknown Industry"
        missing.append("industry")

    size = (biz.size or "").strip() if biz else ""
    if not size or size.lower() in ["unknown", "n/a"]:
        size = "Not Provided"
        missing.append("business_size")

    location = (biz.location or "").strip() if biz else ""
    if not location or location.lower() in ["unknown", "n/a"]:
        location = "Not Provided"
        missing.append("location")

    # Application metadata
    app_name = (app.name or "").strip()
    if not app_name:
        app_name = "AI System"
        missing.append("application_name")

    purpose = (app.purpose or "").strip()
    if not purpose or purpose.lower() in ["unknown", "n/a"]:
        purpose = "Not Provided"
        missing.append("purpose")

    b_func = (app.business_function or "").strip()
    if not b_func or b_func.lower() in ["unknown", "n/a"]:
        b_func = "Not Provided"
        missing.append("business_function")

    data_types = (app.data_types or "").strip()
    if not data_types or data_types.lower() in ["unknown", "n/a"]:
        data_types = "Not Provided"
        missing.append("data_types")

    impact = (app.automated_decision_impact or "").strip()
    if not impact:
        impact = "Unknown"
        missing.append("automated_decision_impact")

    oversight = (app.human_oversight or "").strip()
    if not oversight:
        oversight = "Unknown"
        missing.append("human_oversight")

    model_type = (app.model_type or "").strip()
    if not model_type:
        model_type = "Not Provided"
        missing.append("model_type")

    stakeholders = getattr(app, "affected_stakeholders", None) or "Not Provided"
    if stakeholders in ["Not Provided", "Unknown", ""]:
        stakeholders = "Not Provided"
        missing.append("affected_stakeholders")

    ext_services = getattr(app, "external_services", None) or "Not Provided"
    if ext_services in ["Not Provided", "Unknown", ""]:
        ext_services = "Not Provided"
        missing.append("external_services")

    infra = getattr(app, "infrastructure_type", None) or "Unknown"
    if infra in ["Unknown", "Not Provided", ""]:
        infra = "Unknown"
        missing.append("infrastructure_type")

    # Check for empirical scans and datasets
    fairness = db.query(FairnessResult).filter(FairnessResult.application_id == application_id).order_by(FairnessResult.id.desc()).first()
    privacy = db.query(PrivacyFinding).filter(PrivacyFinding.application_id == application_id).order_by(PrivacyFinding.id.desc()).first()
    sustainability = db.query(SustainabilityResult).filter(SustainabilityResult.application_id == application_id).order_by(SustainabilityResult.id.desc()).first()

    fairness_details = None
    if fairness:
        ds_name = "Benchmark Dataset"
        if fairness.dataset_id:
            ds = db.query(Dataset).filter(Dataset.id == fairness.dataset_id).first()
            if ds and ds.filename:
                ds_name = ds.filename
        fairness_details = {
            "dataset_name": ds_name,
            "sensitive_attribute": fairness.sensitive_attribute,
            "disparity_ratio": fairness.demographic_parity_ratio,
            "disparity_diff": fairness.demographic_parity_diff,
            "risk": fairness.risk_level
        }

    privacy_details = None
    if privacy:
        ds_name = "Ingestion Stream"
        if privacy.dataset_id:
            ds = db.query(Dataset).filter(Dataset.id == privacy.dataset_id).first()
            if ds and ds.filename:
                ds_name = ds.filename
        privacy_details = {
            "dataset_name": ds_name,
            "pii_count": privacy.pii_detected_count,
            "records": privacy.total_records_scanned,
            "risk": privacy.risk_level
        }

    sustainability_details = None
    if sustainability:
        sustainability_details = {
            "kwh": sustainability.energy_kwh,
            "co2e": sustainability.estimated_co2e_kg,
            "region": sustainability.region_name,
            "hours": sustainability.compute_duration_hours
        }

    return BusinessContext(
        business_id=biz_id,
        business_name=biz_name,
        industry=industry,
        size=size,
        location=location,
        application_id=app.id,
        application_name=app_name,
        purpose=purpose,
        business_function=b_func,
        data_types=data_types,
        automated_decision_impact=impact,
        human_oversight=oversight,
        model_type=model_type,
        affected_stakeholders=stakeholders,
        external_services=ext_services,
        infrastructure_type=infra,
        missing_fields=missing,
        has_fairness_scan=fairness is not None,
        has_privacy_scan=privacy is not None,
        has_sustainability_scan=sustainability is not None,
        fairness_details=fairness_details,
        privacy_details=privacy_details,
        sustainability_details=sustainability_details
    )


# ---------------------------------------------------------------------------
# 2. EVIDENCE ATTRIBUTION & ACCURACY RULES
# ---------------------------------------------------------------------------

def determine_evidence_attribution(
    rule_ref: str,
    dimension: str,
    answer: str,
    notes: str,
    context: BusinessContext,
    is_auditor_verified: bool = False
) -> Tuple[str, str, bool]:
    """
    Evidence Attribution Rules:
    1. Only evidence that has passed a defined verification process may be labelled 'Verified'.
    2. Dataset analysis must identify the dataset and analysis performed.
    3. Uploaded documents must be labelled 'Document-derived' until validated.
    4. Hardware compute telemetry is labelled 'System configuration'.
    5. Self-reported answers must be labelled 'Self-reported / Unverified'.
    """
    if is_auditor_verified:
        return "Verified", f"Verified through formal audit verification on {datetime.datetime.utcnow().strftime('%Y-%m-%d')}.", True

    notes_clean = (notes or "").strip()
    notes_lower = notes_clean.lower()

    # 1. Dataset analysis
    if dimension == "fairness" and context.has_fairness_scan and context.fairness_details:
        fd = context.fairness_details
        evidence_text = (
            f"Dataset analysis (Dataset: '{fd.get('dataset_name', 'Primary Benchmark')}'): "
            f"Fairlearn demographic parity analysis across sensitive attribute '{fd.get('sensitive_attribute', 'demographics')}'. "
            f"Observed demographic parity ratio = {fd.get('disparity_ratio', 0.0):.3f}, "
            f"disparity difference = {fd.get('disparity_diff', 0.0):.3f} (Risk tier: {fd.get('risk', 'Moderate')})."
        )
        return "Dataset analysis", evidence_text, False

    if dimension == "privacy" and context.has_privacy_scan and context.privacy_details:
        pd = context.privacy_details
        evidence_text = (
            f"Dataset analysis (Dataset: '{pd.get('dataset_name', 'Input Records')}'): "
            f"Automated PII screening detected {pd.get('pii_count', 0)} unredacted sensitive identifiers "
            f"across {pd.get('records', 0)} scanned records (Risk tier: {pd.get('risk', 'Moderate')})."
        )
        return "Dataset analysis", evidence_text, False

    if dimension == "sustainability" and context.has_sustainability_scan and context.sustainability_details:
        sd = context.sustainability_details
        evidence_text = (
            f"System configuration: Empirical compute runtime telemetry of {sd.get('hours', 0.0)}h "
            f"in region '{sd.get('region', 'Global Average')}' consumed {sd.get('kwh', 0.0):.2f} kWh, "
            f"generating estimated ~{sd.get('co2e', 0.0):.2f} kg CO2e emissions."
        )
        return "System configuration", evidence_text, False

    # 2. Document-derived reference
    doc_keywords = [".pdf", ".docx", ".doc", ".xlsx", ".csv", "document", "uploaded", "policy", "handbook", "attestation", "sop", "certificate"]
    if any(k in notes_lower for k in doc_keywords):
        evidence_text = f"Document-derived: Reference cited in submission: \"{notes_clean}\". Pending independent compliance validation."
        return "Document-derived", evidence_text, False

    # 3. Default: Self-reported / Unverified
    evidence_text = f"Self-reported / Unverified: Question {rule_ref} answered '{answer}'."
    if notes_clean:
        # Preserve the submitter's wording, but never let a self-asserted
        # "verified" claim be mistaken for independent verification.
        evidence_text += f" Submitter note (not independently verified): \"{notes_clean}\"."
    else:
        evidence_text += " No external supporting documentation submitted."

    return "Self-reported / Unverified", evidence_text, False


# ---------------------------------------------------------------------------
# 3. UNIVERSAL RISK SCORING METHODOLOGY
# ---------------------------------------------------------------------------

class RiskScoringModel:
    """
    Standardized, auditable multi-factor risk calculation methodology:
    Residual Risk Score = 100 * (Likelihood/5) * (Impact/5) * Exposure / Control_Effectiveness
    Normalized strictly to [1.0, 100.0].
    
    Factors:
    - Likelihood (1.0 to 5.0): Probability of deficiency leading to an incident or non-compliance.
    - Impact (1.0 to 5.0): Severity of harm if incident occurs (dynamically evaluated based on
      question topic, decision impact, data sensitivity, and affected stakeholders).
      Question IDs (P1, F1, T1, S1) influence risk identification dynamically;
      no question is blindly marked Critical.
    - Exposure (0.8 to 1.4): Scope and vulnerability of user cohort / operational environment.
    - Control Effectiveness (0.6 to 1.4): Existing human oversight and mitigation safeguards.
    """

    @classmethod
    def calculate(
        cls,
        question_ref: str,
        dimension: str,
        context: BusinessContext,
        answer: str,
        notes: str = ""
    ) -> Tuple[str, float, str, str, str, str, str]:
        """
        Calculates:
        (severity, score, likelihood_label, impact_label, exposure_label, control_label, explanation)
        """
        # 1. Likelihood Factor (1.0 - 5.0)
        if answer == "No":
            l_num = 4.0
            l_label = "High"
            # Elevate if completely unassisted and high-impact
            if context.is_unassisted and context.is_high_impact:
                l_num = 4.8
                l_label = "Critical"
        elif answer == "Partially":
            l_num = 2.5
            l_label = "Medium"
        else:  # Yes
            l_num = 1.0
            l_label = "Low"

        # Empirical scan override if empirical disparity or vulnerability exists
        if dimension == "fairness" and context.has_fairness_scan and context.fairness_details:
            if context.fairness_details.get("risk") in ["High", "Critical"]:
                l_num = 5.0
                l_label = "Critical"
        elif dimension == "privacy" and context.has_privacy_scan and context.privacy_details:
            if context.privacy_details.get("pii_count", 0) > 0:
                l_num = 4.8
                l_label = "Critical"

        # 2. Dynamic Impact Factor (1.0 - 5.0)
        # Evaluated contextually based on topic + data types + decision impact
        data_summary = "Non-sensitive / operational" if context.has_non_sensitive_data_only else (
            "Sensitive PII / Special Category" if context.has_sensitive_data else "General / Not Specified"
        )
        
        if dimension == "privacy":
            # P1: PII Minimization, P4: Encryption, P3: Data Retention, P2: Access Control, P5: Third-party
            if context.has_sensitive_data:
                # Sensitive medical, financial, candidate, or personal data
                if question_ref in ["P1", "P4"]:
                    i_num = 4.8
                    i_label = "Critical"
                elif question_ref in ["P2", "P3"]:
                    i_num = 4.0
                    i_label = "High"
                else:  # P5
                    ext_str = (context.external_services or "").lower()
                    if "none" in ext_str or "local" in ext_str:
                        i_num = 2.0
                        i_label = "Low"
                    else:
                        i_num = 4.0
                        i_label = "High"
            elif context.has_non_sensitive_data_only:
                # Machine sensor data, vehicle telemetry, public catalog, etc.
                if question_ref in ["P1", "P4"]:
                    i_num = 2.0
                    i_label = "Low"
                else:
                    i_num = 1.8
                    i_label = "Low"
            else:
                # Incomplete or general data types
                i_num = 3.0
                i_label = "Medium"

        elif dimension == "fairness":
            # F1: Pre-deployment bias, F2: Runtime drift, F3: Appeal, F4: Proxies, F5: Containment
            if context.is_high_impact:
                # Decisions affecting civil rights, livelihood, employment, credit, healthcare
                if question_ref in ["F1", "F2"]:
                    i_num = 4.8
                    i_label = "Critical"
                else:
                    i_num = 4.0
                    i_label = "High"
            elif (context.automated_decision_impact or "").lower() == "low":
                # Low-impact recommendation, dev tooling, vehicle wax recommendation
                i_num = 1.8
                i_label = "Low"
            else:
                i_num = 3.0
                i_label = "Medium"

        elif dimension == "transparency":
            # T1: Explainability, T5: Human oversight, T2: Disclosure, T3: Audit logs, T4: Performance
            if context.is_high_impact and context.is_unassisted:
                if question_ref in ["T1", "T5"]:
                    i_num = 4.8
                    i_label = "Critical"
                else:
                    i_num = 4.0
                    i_label = "High"
            elif (context.automated_decision_impact or "").lower() == "low":
                i_num = 2.0
                i_label = "Low"
            else:
                i_num = 3.0
                i_label = "Medium"

        else:  # sustainability
            # S1: Energy tracking, S2: Idle scaling, S3: Caching, S4: Architecture, S5: Clean hosting
            infra_str = (context.infrastructure_type or "").lower()
            if "gpu" in infra_str or "cluster" in infra_str or "datacenter" in infra_str:
                i_num = 3.5
                i_label = "Medium"
            elif "edge" in infra_str or "cpu" in infra_str or "local" in infra_str:
                i_num = 1.6
                i_label = "Low"
            else:
                if question_ref in ["S1", "S2"]:
                    i_num = 2.8
                    i_label = "Medium"
                else:
                    i_num = 2.0
                    i_label = "Low"

        # 3. Exposure Factor (0.85 - 1.35)
        st_desc = context.stakeholder_description.lower()
        if any(w in st_desc for w in ["patient", "minor", "children", "candidate", "borrower", "applicant"]):
            exp_num = 1.35
            exp_label = "High (Vulnerable / Impacted Cohort)"
        elif any(w in st_desc for w in ["customer", "client", "consumer", "vehicle owner", "public"]):
            exp_num = 1.15
            exp_label = "Medium (External Public / Clients)"
        elif any(w in st_desc for w in ["employee", "internal", "staff", "technician"]):
            exp_num = 1.00
            exp_label = "Moderate (Internal Enterprise Users)"
        else:
            exp_num = 0.85
            exp_label = "Low (Developer / Local / Test Bench)"

        # 4. Control Effectiveness Factor (0.60 - 1.35)
        ov_str = (context.human_oversight or "").lower()
        if "loop" in ov_str and "in" in ov_str:
            c_base = 1.25
            c_label = "Strong (Human-in-the-loop)"
        elif "loop" in ov_str and "on" in ov_str:
            c_base = 1.10
            c_label = "Moderate (Human-on-the-loop)"
        elif "none" in ov_str or "unassisted" in ov_str or "autonomous" in ov_str:
            c_base = 0.80
            c_label = "Weak (Autonomous / Unassisted)"
        else:
            c_base = 1.00
            c_label = "Baseline / Standard"

        # Adjust for answer
        if answer == "No":
            c_num = max(0.60, c_base - 0.20)
            c_label += " [No Specific Safeguard]"
        elif answer == "Partially":
            c_num = max(0.70, c_base)
            c_label += " [Partial Safeguard Active]"
        else:
            c_num = min(1.40, c_base + 0.20)
            c_label += " [Safeguard Implemented]"

        # 5. Composite Risk Calculation
        # Transparent 0-100 formula:
        #   100 * (likelihood / 5) * (impact / 5) * exposure / control_factor
        # Exposure > 1 increases risk. A larger control_factor represents
        # stronger safeguards and therefore reduces residual risk.
        # No unexplained calibration multiplier is used.
        raw_score = (
            100.0
            * (l_num / 5.0)
            * (i_num / 5.0)
            * exp_num
            / max(c_num, 0.01)
        )
        composite_score = round(min(100.0, max(0.0, raw_score)), 1)

        # 6. Consistent severity thresholds applied everywhere.
        if composite_score >= 75.0:
            severity = "Critical"
        elif composite_score >= 50.0:
            severity = "High"
        elif composite_score >= 25.0:
            severity = "Medium"
        else:
            severity = "Low"

        # 7. Auditable Explanation
        explanation = (
            f"Evaluated via Likelihood={l_label} ({l_num:.1f}), "
            f"Impact={i_label} ({i_num:.1f}, derived from question {question_ref}, data sensitivity '{data_summary}', and decision impact '{context.automated_decision_impact}'), "
            f"Exposure={exp_label} ({exp_num:.2f}, cohort: '{context.stakeholder_description}'), and "
            f"Control Effectiveness={c_label} ({c_num:.2f}, oversight tier '{context.human_oversight}'). "
            f"Yields composite risk index {composite_score}/100 -> Severity: {severity}. (Internal SME governance index; not statutory certification)."
        )

        return severity, composite_score, l_label, i_label, exp_label, c_label, explanation


# ---------------------------------------------------------------------------
# 4. CONTEXT-AWARE, TECHNOLOGY-NEUTRAL RECOMMENDATION GENERATORS
# ---------------------------------------------------------------------------

@dataclass
class UniversalRuleDefinition:
    rule_key: str
    dimension: str  # "fairness", "transparency", "privacy", "sustainability"
    question_id_ref: str  # e.g., "F1", "T1", "P1", "S1"
    title_template: str
    impact_template: str
    generator_fn: Any  # Callable[[BusinessContext, str, str], Tuple[str, str, str]]


def _build_neutral_rec(base_action: str, context: BusinessContext, needed_details: List[str]) -> str:
    """Appends explicit statement of missing context if technical specifics are unknown."""
    if not needed_details:
        return base_action
    missing_str = ", ".join(needed_details)
    return f"{base_action} [Note: To specify exact deployment tooling or commands, additional business context is required: {missing_str}]."


# --- FAIRNESS RECOMMENDATION GENERATORS ---
def _rec_f1_bias_testing(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Pre-Deployment Algorithmic Bias Exposure ({ctx.industry})"
    impact = (
        f"Deploying {ctx.application_name} without pre-deployment subgroup testing risks disparate outcomes "
        f"across {ctx.stakeholder_description}, creating compliance exposure and stakeholder mistrust."
    )
    needed = []
    if "data_types" in ctx.missing_fields:
        needed.append("processed feature schema and demographics")
    
    prefix = "While preliminary evaluation has begun, " if ans == "Partially" else ""
    action = (
        f"{prefix}Conduct empirical disparate impact analysis across key user cohorts for {ctx.application_name}. "
        f"Establish baseline parity metrics (such as demographic parity difference and selection rate variance) "
        f"before approving automated outputs for operational use."
    )
    return title, impact, _build_neutral_rec(action, ctx, needed)


def _rec_f2_runtime_drift(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Unmonitored Algorithmic Bias Drift ({ctx.application_name})"
    impact = (
        f"Without recurring monitoring, {ctx.application_name} may silently develop bias drift as operational "
        f"patterns and {ctx.stakeholder_description} demographics change over time."
    )
    action = (
        f"Establish a scheduled review cadence (e.g. monthly or quarterly) evaluating outcome parity ratios "
        f"against historical baselines for {ctx.application_name}."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


def _rec_f3_appeal_mechanism(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Absence of User Dispute and Redress Channel"
    impact = (
        f"Without an accessible appeal mechanism, disputed automated decisions from {ctx.application_name} "
        f"cannot be contested by {ctx.stakeholder_description}, escalating consumer disputes and operational friction."
    )
    action = (
        f"Establish an accessible dispute process allowing {ctx.stakeholder_description} to contest automated decisions "
        f"and request review by a qualified human representative within a defined response window."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


def _rec_f4_proxy_variables(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Undocumented Proxy Feature Vulnerability"
    impact = (
        f"Hidden proxy variables in {ctx.data_types} can inadvertently re-introduce protected demographic biases "
        f"into {ctx.application_name}'s automated recommendations."
    )
    action = (
        f"Audit input features in {ctx.application_name} for statistical correlation with sensitive attributes. "
        f"Document identified proxy relationships and justifiable model trade-offs in an internal system card."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


def _rec_f5_remediation_plan(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Lack of Documented Bias Disparity Thresholds and Containment Plan"
    impact = (
        f"If {ctx.application_name} demonstrates outcome disparities in production, the absence of predefined triggers "
        f"prevents swift operational pause or remediation, compounding compliance liabilities."
    )
    action = (
        f"Define quantitative disparity containment thresholds that mandate an immediate review or temporary fallback "
        f"to manual processing whenever automated decision variance exceeds acceptable tolerances."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


# --- TRANSPARENCY RECOMMENDATION GENERATORS ---
def _rec_t1_explainability(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Opaque Decision Rationale (Black-Box AI System)"
    impact = (
        f"Operating {ctx.application_name} without interpretable local and global feature explanations leaves operators "
        f"unable to justify individual automated outcomes to {ctx.stakeholder_description} or review inquiries."
    )
    needed = []
    if "model_type" in ctx.missing_fields:
        needed.append("model architecture type")
    action = (
        f"Integrate interpretable feature attribution methods (such as local feature weightings or score decomposition) "
        f"so operators and affected individuals can inspect the primary factors determining automated outcomes."
    )
    return title, impact, _build_neutral_rec(action, ctx, needed)


def _rec_t2_user_disclosure(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Inadequate AI Involvement Disclosure"
    impact = (
        f"Failing to inform {ctx.stakeholder_description} when interacting with or being evaluated by an automated AI system "
        f"violates consumer transparency expectations and emerging statutory disclosure mandates."
    )
    action = (
        f"Provide prominent, clear notifications across user interfaces and communications disclosing that automated "
        f"AI processing plays a material role in {ctx.application_name}."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


def _rec_t3_audit_logging(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Incomplete Automated Decision Audit Trail"
    impact = (
        f"Without immutable logs recording inputs, timestamps, model identifiers, and confidence scores for {ctx.application_name}, "
        f"reconstructing historical decisions during disputes or internal reviews is impossible."
    )
    needed = []
    if not ctx.known_infrastructure:
        needed.append("database / storage architecture")
    action = (
        f"Implement append-only decision audit logging capturing input parameters, model version, timestamp, "
        f"and output predictions for every execution of {ctx.application_name}."
    )
    return title, impact, _build_neutral_rec(action, ctx, needed)


def _rec_t4_performance_monitoring(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Absence of Ground-Truth Performance Verification"
    impact = (
        f"Without periodic performance verification against ground-truth outcomes, degradation in {ctx.application_name}'s "
        f"accuracy remains undetected, causing silent business operational failures."
    )
    action = (
        f"Establish a recurring benchmark comparing automated predictions against verified real-world operational results "
        f"to detect concept drift and accuracy decay."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


def _rec_t5_human_oversight(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Deficient Human-in-the-Loop Oversight for High-Impact Decisions"
    impact = (
        f"Permitting high-stakes automated decisions from {ctx.application_name} to execute without qualified human review "
        f"creates critical exposure to automated errors, hallucinations, and uncontrolled business liability."
    )
    action = (
        f"Institute a mandatory human-in-the-loop review policy empowering designated staff to validate, hold, "
        f"or override automated determinations from {ctx.application_name} before they take effect."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


# --- PRIVACY RECOMMENDATION GENERATORS ---
def _rec_p1_data_minimization(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    data_label = "operational data" if ctx.has_non_sensitive_data_only else "personal identifiers"
    title = f"Unredacted Sensitive Data & Ingestion Non-Minimization"
    impact = (
        f"Processing unmasked {data_label} in {ctx.data_types} through {ctx.application_name} "
        f"magnifies privacy exposure and compliance penalties in the event of an unauthorized data spill."
    )
    action = (
        f"Deploy a data screening and sanitization filter at the input ingestion gateway to mask, hash, "
        f"or discard unnecessary personal identifiers before data is stored or processed by {ctx.application_name}."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


def _rec_p2_access_control(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Permissive Internal Access to AI Datasets and Model Assets"
    impact = (
        f"Inadequate access restrictions to training datasets, inference logs, or model parameters create insider threat "
        f"vulnerabilities and unmonitored data exfiltration risks."
    )
    action = (
        f"Enforce granular Role-Based Access Controls (RBAC) and Multi-Factor Authentication (MFA) across all repositories, "
        f"databases, and endpoints that store or process operational data for {ctx.application_name}."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


def _rec_p3_data_retention(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Indefinite Data Retention and Undefined Disposal Schedule"
    impact = (
        f"Hoarding legacy user inquiries, temporary session inputs, and operational logs beyond necessary business duration "
        f"violates storage limitation mandates and compounds legal discovery exposure."
    )
    action = (
        f"Establish a formal data retention schedule with automated purge routines to permanently delete or anonymize "
        f"temporary inputs and operational logs once their legitimate business purpose has concluded."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


def _rec_p4_encryption(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Unverified Cryptographic Protections in Transit and at Rest"
    impact = (
        f"Transmitting or storing operational data without verified modern encryption exposes {ctx.business_name} "
        f"to interception, unauthorized access, and data breach liabilities."
    )
    action = (
        f"Verify and enforce modern cryptographic protection across all communication channels (TLS 1.3/HTTPS) and "
        f"enable strong encryption at rest (such as AES-256) for all persistent volumes holding {ctx.application_name} data."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


def _rec_p5_third_party_vetting(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Unvetted External Sub-Processors and AI Services"
    ext_str = (ctx.external_services or "").lower()
    is_purely_local = "none" in ext_str or "local" in ext_str
    
    impact = (
        f"Utilizing external AI APIs, hosting platforms, or sub-processors without documented data protection agreements "
        f"leaves {ctx.business_name} legally liable for third-party privacy violations and unauthorized model retraining."
        if not is_purely_local else
        f"Operating with undocumented sub-processor boundaries risks unmonitored outbound API calls and data leakage."
    )
    needed = []
    if "external_services" in ctx.missing_fields:
        needed.append("list of external third-party AI APIs or vendor sub-processors")
    
    action = (
        f"Execute formal Data Processing Agreements (DPAs) with all external software and AI model vendors, verifying "
        f"contractually that enterprise data will not be retained or used to train third-party foundational models."
        if not is_purely_local else
        f"Maintain an explicit hardware and vendor inventory verifying that {ctx.application_name} runs in an isolated local environment with zero unauthorized outbound data transmission."
    )
    return title, impact, _build_neutral_rec(action, ctx, needed)


# --- SUSTAINABILITY RECOMMENDATION GENERATORS ---
def _rec_s1_energy_tracking(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Unmeasured AI Compute Energy Consumption and Carbon Emissions"
    impact = (
        f"Without tracking compute-hours, electricity consumption, and operational carbon metrics for {ctx.application_name}, "
        f"{ctx.business_name} cannot quantify or optimize operational cloud expenditure or environmental impact."
    )
    needed = []
    if not ctx.known_infrastructure:
        needed.append("hosting infrastructure environment")
    action = (
        f"Implement baseline compute telemetry tracking processor runtime hours and estimated kilowatt-hours (kWh) "
        f"for workloads associated with {ctx.application_name}."
    )
    return title, impact, _build_neutral_rec(action, ctx, needed)


def _rec_s2_idle_compute(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Resource Over-Provisioning and Idle Compute Waste"
    impact = (
        f"Maintaining continuous server capacity during prolonged periods of low or zero user demand generates "
        f"unnecessary operational expenses and avoidable Scope 2 carbon emissions."
    )
    needed = []
    if not ctx.known_infrastructure:
        needed.append("server deployment platform")
    action = (
        f"Configure automated scaling policies or scheduled shutdown routines to dynamically scale compute instances "
        f"down or to zero during non-operational hours and low-traffic windows."
    )
    return title, impact, _build_neutral_rec(action, ctx, needed)


def _rec_s3_inference_caching(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Redundant Re-Computation and Un-Cached Model Inference"
    impact = (
        f"Executing repeated identical model inferences for common inputs wastes processor capacity, degrades user response "
        f"latencies, and multiplies compute costs."
    )
    action = (
        f"Implement a localized caching tier for frequent or identical model queries to serve recurrent results "
        f"without triggering full model re-evaluation."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


def _rec_s4_model_efficiency(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Excessive Model Architecture Complexity and Energy Overhead"
    impact = (
        f"Deploying oversized foundation networks where compact, domain-specialized models achieve equivalent operational accuracy "
        f"substantially increases inference latency, server energy requirements, and financial overhead."
    )
    action = (
        f"Benchmark task accuracy across lightweight, optimized architectures (such as quantized, distilled, or classical machine learning models) "
        f"before committing to resource-intensive large-scale networks for {ctx.application_name}."
    )
    return title, impact, _build_neutral_rec(action, ctx, [])


def _rec_s5_green_hosting(ctx: BusinessContext, ans: str, notes: str) -> Tuple[str, str, str]:
    title = f"Deployment in High-Carbon Grid Intensity Regions"
    impact = (
        f"Hosting compute workloads in geographical zones dependent on fossil fuels magnifies operational greenhouse "
        f"gas emissions compared to renewable-powered cloud regions."
    )
    needed = []
    if not ctx.known_infrastructure:
        needed.append("cloud provider / data center locations")
    action = (
        f"Evaluate the carbon intensity of current data centers hosting {ctx.application_name} and plan workload "
        f"placement in facilities or regions with verified high percentages of clean, renewable energy."
    )
    return title, impact, _build_neutral_rec(action, ctx, needed)


# ---------------------------------------------------------------------------
# 5. UNIVERSAL RULES REGISTRY (20 Core Governance Criteria)
# ---------------------------------------------------------------------------

UNIVERSAL_RULES: List[UniversalRuleDefinition] = [
    # Fairness
    UniversalRuleDefinition("FAIR_PRE_DEPLOYMENT_BIAS", "fairness", "F1", "Pre-Deployment Bias Testing", "", _rec_f1_bias_testing),
    UniversalRuleDefinition("FAIR_RUNTIME_DRIFT", "fairness", "F2", "Operational Bias Drift Monitoring", "", _rec_f2_runtime_drift),
    UniversalRuleDefinition("FAIR_APPEAL_MECHANISM", "fairness", "F3", "User Appeal and Dispute Mechanism", "", _rec_f3_appeal_mechanism),
    UniversalRuleDefinition("FAIR_PROXY_VARIABLES", "fairness", "F4", "Proxy Feature Governance", "", _rec_f4_proxy_variables),
    UniversalRuleDefinition("FAIR_DISPARITY_REMEDIATION", "fairness", "F5", "Disparity Containment Plan", "", _rec_f5_remediation_plan),

    # Transparency
    UniversalRuleDefinition("TRANS_LOCAL_EXPLAINABILITY", "transparency", "T1", "Local Decision Interpretability", "", _rec_t1_explainability),
    UniversalRuleDefinition("TRANS_USER_DISCLOSURE", "transparency", "T2", "AI System Disclosure", "", _rec_t2_user_disclosure),
    UniversalRuleDefinition("TRANS_AUDIT_LOGGING", "transparency", "T3", "Immutable Audit Logging", "", _rec_t3_audit_logging),
    UniversalRuleDefinition("TRANS_PERFORMANCE_DRIFT", "transparency", "T4", "Performance Drift Tracking", "", _rec_t4_performance_monitoring),
    UniversalRuleDefinition("TRANS_HUMAN_OVERSIGHT", "transparency", "T5", "Human-in-the-Loop Oversight", "", _rec_t5_human_oversight),

    # Privacy
    UniversalRuleDefinition("PRIV_DATA_MINIMIZATION", "privacy", "P1", "PII Minimization and Screening", "", _rec_p1_data_minimization),
    UniversalRuleDefinition("PRIV_ACCESS_CONTROL", "privacy", "P2", "Granular Access Control & MFA", "", _rec_p2_access_control),
    UniversalRuleDefinition("PRIV_DATA_RETENTION", "privacy", "P3", "Automated Data Retention Schedule", "", _rec_p3_data_retention),
    UniversalRuleDefinition("PRIV_ENCRYPTION", "privacy", "P4", "End-to-End Cryptographic Security", "", _rec_p4_encryption),
    UniversalRuleDefinition("PRIV_THIRD_PARTY_VETTING", "privacy", "P5", "Sub-Processor & AI Vendor Vetting", "", _rec_p5_third_party_vetting),

    # Sustainability
    UniversalRuleDefinition("SUST_ENERGY_TRACKING", "sustainability", "S1", "Compute Energy & Carbon Tracking", "", _rec_s1_energy_tracking),
    UniversalRuleDefinition("SUST_IDLE_COMPUTE", "sustainability", "S2", "Idle Instance Scaling", "", _rec_s2_idle_compute),
    UniversalRuleDefinition("SUST_INFERENCE_CACHING", "sustainability", "S3", "Inference Result Caching", "", _rec_s3_inference_caching),
    UniversalRuleDefinition("SUST_MODEL_EFFICIENCY", "sustainability", "S4", "Lightweight Architecture Benchmarking", "", _rec_s4_model_efficiency),
    UniversalRuleDefinition("SUST_GREEN_HOSTING", "sustainability", "S5", "Low-Carbon Regional Hosting", "", _rec_s5_green_hosting),
]


# ---------------------------------------------------------------------------
# 6. CENTRAL RISK INTELLIGENCE ENGINE CLASS
# ---------------------------------------------------------------------------

class RiskIntelligenceEngine:
    """
    Centralized, business-agnostic Risk Intelligence Engine.
    Executes universal evaluation, scoring, deduplication, lifecycle tracking,
    and remediation management across all SME businesses and AI applications.
    """

    @classmethod
    def evaluate_and_sync(
        cls,
        db: Session,
        application_id: int,
        assessment_id: Optional[int] = None,
        responses: Optional[List[Dict[str, Any]]] = None,
        actor_email: Optional[str] = None
    ) -> Tuple[List[Risk], List[Recommendation]]:
        """
        Main engine entrypoint:
        1. Extracts business and application context (safely flagging missing values).
        2. Evaluates universal rules against submitted answers or database records.
        3. Prevents duplicates within the run.
        4. Tracks lifecycle across historical assessments (New, Repeated, Improved, Resolved, Reopened).
        5. Persists Risk records with complete audit trails and remediation workflows.
        6. Synchronizes matching context-aware Recommendations.
        """
        context = extract_business_context(db, application_id)
        now = datetime.datetime.utcnow()
        actor = actor_email or "system_risk_engine"

        # Map current answers by question_id (e.g., "F1", "T1", "P1", "S1")
        answers_map: Dict[str, Dict[str, Any]] = {}
        if responses is not None:
            for r in responses:
                q_id = (r.get("question_id") or "").strip()
                if q_id:
                    # Last submitted response for a question is authoritative.
                    answers_map[q_id] = r
        elif assessment_id:
            db_resps = db.query(AssessmentResponse).filter(AssessmentResponse.assessment_id == assessment_id).all()
            for r in db_resps:
                answers_map[r.question_id] = {
                    "question_id": r.question_id,
                    "answer": r.answer,
                    "notes": r.notes or "",
                    "guidance": r.guidance or "",
                    "evidence_required": r.evidence_required or ""
                }

        # Retrieve existing risks for this application to manage lifecycle states
        prior_risks = db.query(Risk).filter(Risk.application_id == application_id).all()
        prior_risk_map: Dict[str, Risk] = {}
        for pr in prior_risks:
            key = pr.risk_key or pr.title
            prior_risk_map[key] = pr

        active_risks: List[Risk] = []
        active_recs: List[Recommendation] = []
        emitted_keys = set()

        for rule in UNIVERSAL_RULES:
            if rule.rule_key in emitted_keys:
                continue

            # Never interpret an unanswered question as "No". Partial payloads
            # must not create findings or resolve risks for questions not supplied.
            resp = answers_map.get(rule.question_id_ref)
            if resp is None:
                continue

            ans = str(resp.get("answer", "")).strip()
            notes = str(resp.get("notes", "") or "").strip()
            if ans not in {"Yes", "No", "Partially", "N/A"}:
                continue
            # N/A is not evidence of compliance or non-compliance. Leave any
            # existing finding unchanged until a valid answer is provided.
            if ans == "N/A":
                continue

            # If compliant (Yes) and a prior risk existed, resolve it
            if ans == "Yes":
                if rule.rule_key in prior_risk_map:
                    prior = prior_risk_map[rule.rule_key]
                    if prior.status != "Resolved":
                        prior.status = "Resolved"
                        prior.lifecycle_status = "Resolved"
                        prior.completion_notes = f"Verified addressed in assessment #{assessment_id or 'latest'} on {now.strftime('%Y-%m-%d')}."
                        hist = cls._parse_history(prior.remediation_history_json)
                        hist.append({
                            "timestamp": now.isoformat(),
                            "action": "Resolved",
                            "status": "Resolved",
                            "user": actor,
                            "notes": prior.completion_notes
                        })
                        prior.remediation_history_json = json.dumps(hist)
                        prior.updated_at = now
                        db.add(prior)
                continue

            # If deficient (No or Partially), evaluate risk
            if ans in ["No", "Partially"]:
                emitted_keys.add(rule.rule_key)

                # Generate context-aware finding and recommendation
                title, impact, rec_action = rule.generator_fn(context, ans, notes)

                # Compute standardized severity and score dynamically
                sev, score, l_lbl, i_lbl, exp_lbl, c_lbl, explanation = RiskScoringModel.calculate(
                    question_ref=rule.question_id_ref,
                    dimension=rule.dimension,
                    context=context,
                    answer=ans,
                    notes=notes
                )

                # Determine evidence attribution
                ev_source, evidence_text, is_verified = determine_evidence_attribution(
                    rule_ref=rule.question_id_ref,
                    dimension=rule.dimension,
                    answer=ans,
                    notes=notes,
                    context=context
                )

                # Lifecycle state tracking across assessments
                prior = prior_risk_map.get(rule.rule_key)
                if prior:
                    if prior.status == "Resolved":
                        lifecycle_status = "Reopened"
                    elif prior.risk_score and (prior.risk_score - score >= 15.0):
                        lifecycle_status = "Improved"
                    else:
                        lifecycle_status = "Repeated"

                    risk_obj = prior
                    risk_obj.assessment_id = assessment_id or risk_obj.assessment_id
                    risk_obj.title = title
                    risk_obj.severity = sev
                    risk_obj.risk_score = score
                    risk_obj.likelihood = l_lbl
                    risk_obj.impact = i_lbl
                    risk_obj.exposure_factor = exp_lbl
                    risk_obj.control_effectiveness = c_lbl
                    risk_obj.evidence = evidence_text
                    risk_obj.business_impact = impact
                    risk_obj.recommended_action = rec_action
                    risk_obj.status = "Open" if prior.status == "Resolved" else prior.status
                    risk_obj.lifecycle_status = lifecycle_status
                    risk_obj.evidence_source = ev_source
                    risk_obj.is_verified = is_verified
                    risk_obj.description = f"{rule.title_template} for {context.application_name} in {context.industry}. {explanation}"
                    risk_obj.updated_at = now

                    hist = cls._parse_history(risk_obj.remediation_history_json)
                    hist.append({
                        "timestamp": now.isoformat(),
                        "action": "Updated",
                        "lifecycle_status": lifecycle_status,
                        "status": risk_obj.status,
                        "severity": sev,
                        "score": score,
                        "user": actor
                    })
                    risk_obj.remediation_history_json = json.dumps(hist)
                else:
                    lifecycle_status = "New"
                    initial_hist = [{
                        "timestamp": now.isoformat(),
                        "action": "Created",
                        "lifecycle_status": "New",
                        "status": "Open",
                        "severity": sev,
                        "score": score,
                        "user": actor,
                        "notes": "Generated by Universal Risk Intelligence Engine."
                    }]
                    team_default = "Engineering" if rule.dimension in ["privacy", "sustainability"] else ("Legal & Compliance" if rule.dimension == "fairness" else "HR & Operations")

                    risk_obj = Risk(
                        application_id=application_id,
                        assessment_id=assessment_id,
                        title=title,
                        description=f"{rule.title_template} for {context.application_name} in {context.industry}. {explanation}",
                        source_module=rule.dimension,
                        severity=sev,
                        evidence=evidence_text,
                        business_impact=impact,
                        recommended_action=rec_action,
                        status="Open",
                        risk_key=rule.rule_key,
                        category=rule.dimension,
                        likelihood=l_lbl,
                        impact=i_lbl,
                        exposure_factor=exp_lbl,
                        control_effectiveness=c_lbl,
                        risk_score=score,
                        evidence_source=ev_source,
                        is_verified=is_verified,
                        lifecycle_status="New",
                        responsible_owner=team_default,
                        target_date=(now + datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
                        remediation_history_json=json.dumps(initial_hist),
                        created_at=now,
                        updated_at=now
                    )
                    db.add(risk_obj)

                active_risks.append(risk_obj)

                # Prioritized matching recommendation
                prio_map = {"Critical": "High", "High": "High", "Medium": "Medium", "Low": "Low"}
                recommendation_problem = f"{rule.dimension.title()} Finding: {title[:110]}"
                rec_obj = (
                    db.query(Recommendation)
                    .filter(
                        Recommendation.application_id == application_id,
                        Recommendation.source_module == rule.dimension,
                        Recommendation.problem == recommendation_problem
                    )
                    .order_by(Recommendation.created_at.desc())
                    .first()
                )
                if rec_obj is None:
                    rec_obj = Recommendation(
                        application_id=application_id,
                        assessment_id=assessment_id,
                        problem=recommendation_problem,
                        why_it_matters=impact,
                        action=rec_action,
                        priority=prio_map.get(sev, "Medium"),
                        expected_business_benefit=f"Mitigates {rule.dimension} risk exposure and establishes audit-ready governance for {context.application_name}.",
                        responsible_team="Engineering" if rule.dimension in ["privacy", "sustainability"] else "Legal & Compliance",
                        status="Pending",
                        source_module=rule.dimension
                    )
                    db.add(rec_obj)
                else:
                    rec_obj.assessment_id = assessment_id or rec_obj.assessment_id
                    rec_obj.why_it_matters = impact
                    rec_obj.action = rec_action
                    rec_obj.priority = prio_map.get(sev, "Medium")
                    rec_obj.expected_business_benefit = f"Mitigates {rule.dimension} risk exposure and establishes audit-ready governance for {context.application_name}."
                    rec_obj.responsible_team = "Engineering" if rule.dimension in ["privacy", "sustainability"] else "Legal & Compliance"
                    # Do not silently reset a recommendation already marked Implemented.
                active_recs.append(rec_obj)

        db.commit()
        for r in active_risks:
            db.refresh(r)

        return active_risks, active_recs

    @classmethod
    def update_remediation_status(
        cls,
        db: Session,
        risk_id: int,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        recommended_action: Optional[str] = None,
        responsible_owner: Optional[str] = None,
        target_date: Optional[str] = None,
        completion_notes: Optional[str] = None,
        supporting_evidence: Optional[str] = None,
        is_verified: Optional[bool] = None,
        actor_email: Optional[str] = None
    ) -> Risk:
        """
        Updates remediation status, audit notes, dates, and logs immutable history.
        """
        risk = db.query(Risk).filter(Risk.id == risk_id).first()
        if not risk:
            raise ValueError(f"Risk ID {risk_id} not found.")

        now = datetime.datetime.utcnow()
        actor = actor_email or "system_user"
        hist = cls._parse_history(risk.remediation_history_json)
        changes = []

        if status and status != risk.status:
            changes.append(f"status: '{risk.status}' -> '{status}'")
            risk.status = status
            if status == "Resolved":
                risk.lifecycle_status = "Resolved"
            elif status == "In progress" and risk.lifecycle_status in ["New", "Repeated"]:
                risk.lifecycle_status = "In progress"

        if severity and severity != risk.severity:
            changes.append(f"severity: '{risk.severity}' -> '{severity}'")
            risk.severity = severity

        if recommended_action and recommended_action != risk.recommended_action:
            changes.append("action updated")
            risk.recommended_action = recommended_action

        if responsible_owner and responsible_owner != risk.responsible_owner:
            changes.append(f"owner: '{risk.responsible_owner}' -> '{responsible_owner}'")
            risk.responsible_owner = responsible_owner

        if target_date and target_date != risk.target_date:
            changes.append(f"target_date: '{risk.target_date}' -> '{target_date}'")
            risk.target_date = target_date

        if completion_notes:
            risk.completion_notes = completion_notes
            changes.append("completion notes recorded")

        if supporting_evidence:
            risk.supporting_evidence = supporting_evidence
            changes.append("supporting evidence linked")

        if is_verified is not None:
            risk.is_verified = is_verified
            if is_verified:
                risk.evidence_source = "Verified"
            changes.append(f"is_verified set to {is_verified}")

        if changes:
            hist.append({
                "timestamp": now.isoformat(),
                "action": "Remediation Update",
                "user": actor,
                "changes": ", ".join(changes),
                "notes": completion_notes or ""
            })
            risk.remediation_history_json = json.dumps(hist)
            risk.updated_at = now

        db.commit()
        db.refresh(risk)
        return risk

    @staticmethod
    def _parse_history(raw_json: Optional[str]) -> List[Dict[str, Any]]:
        if not raw_json:
            return []
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return []

# Backwards compatibility alias
UniversalRiskEngine = RiskIntelligenceEngine
