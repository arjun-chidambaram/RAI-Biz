from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
import datetime

# --- Auth Schemas ---
class SendOTPRequest(BaseModel):
    email: str = Field(..., description="User's email address")

class VerifyOTPRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

class ResendOTPRequest(BaseModel):
    email: str = Field(..., description="User's email address")

class DemoLoginRequest(BaseModel):
    email: str = Field(..., description="Predefined Hackathon Demo account email (admin@smarthire.ai or auditor@raibiz.io)")

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str = "Compliance Officer"
    is_verified: bool = False
    created_at: datetime.datetime
    last_login: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

# --- Profile Update Payload ---
class ProfileUpdatePayload(BaseModel):
    name: str
    industry: str
    size: str
    location: str
    description: Optional[str] = None
    contact_email: Optional[str] = None
    app_name: str
    purpose: str
    business_function: str
    data_types: str
    automated_decision_impact: str = "High"
    human_oversight: str = "None"
    affected_stakeholders: Optional[str] = "Not Provided"
    external_services: Optional[str] = "Not Provided"
    infrastructure_type: Optional[str] = "Unknown"

# --- Business ---
class BusinessBase(BaseModel):
    name: str
    industry: str
    size: str
    location: str
    description: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None

class BusinessCreate(BusinessBase):
    pass

class BusinessResponse(BusinessBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

# --- AI Application ---
class AIApplicationBase(BaseModel):
    name: str
    purpose: str
    business_function: str
    data_types: str
    automated_decision_impact: str = "High"
    human_oversight: str = "None"
    model_type: str = "Classification Model"
    affected_stakeholders: Optional[str] = "Not Provided"
    external_services: Optional[str] = "Not Provided"
    infrastructure_type: Optional[str] = "Unknown"
    status: str = "Active"

class AIApplicationCreate(AIApplicationBase):
    business_id: int

class AIApplicationResponse(AIApplicationBase):
    id: int
    business_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Authentication & Profile Responses ---
class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None
    business: Optional[BusinessResponse] = None
    application: Optional[AIApplicationResponse] = None
    csrf_token: Optional[str] = None
    token: Optional[str] = None
    message: Optional[str] = None

class ProfileUpdateResponse(BaseModel):
    success: bool = True
    business: BusinessResponse
    application: Optional[AIApplicationResponse] = None
    message: str = "Profile and AI Application successfully updated."

# --- Assessment ---
class QuestionOption(BaseModel):
    label: str
    score: Optional[float]

class QuestionDefinition(BaseModel):
    id: str
    category: str  # "fairness", "transparency", "privacy", "sustainability"
    category_title: str
    industry: Optional[str] = "General"
    ai_application_context: Optional[str] = None
    question_text: str
    why_it_matters: str
    guidance: str
    evidence_required: Optional[str] = None
    risk_category: Optional[str] = None
    risk_severity: Optional[str] = "High"
    answer_options: List[str] = ["Yes", "Partially", "No", "N/A"]
    recommendation: Optional[str] = None

class GenerateQuestionsRequest(BaseModel):
    application_id: Optional[int] = None
    force_llm: Optional[bool] = False

class DynamicQuestionSetResponse(BaseModel):
    business_id: int
    application_id: int
    business_name: str
    application_name: str
    industry: str
    industry_key: str
    generation_source: str = "curated_domain_engine"
    dimensions: List[str] = ["fairness", "transparency", "privacy", "sustainability"]
    question_count: int
    questions: List[QuestionDefinition]

class AssessmentResponseInput(BaseModel):
    question_id: str
    category: Optional[str] = None
    question_text: Optional[str] = None
    answer: str  # "Yes", "Partially", "No", "N/A"
    notes: Optional[str] = None
    guidance: Optional[str] = None
    evidence_required: Optional[str] = None
    risk_severity: Optional[str] = None
    recommendation: Optional[str] = None

class AssessmentCreate(BaseModel):
    business_id: int
    application_id: int
    name: str = "Comprehensive SME RAI Governance Audit"
    industry: Optional[str] = None
    notes: Optional[str] = None
    responses: List[AssessmentResponseInput]

class DimensionScore(BaseModel):
    dimension: str
    score: float
    status: str
    answered_count: int
    total_count: int

class AssessmentResponseDetail(BaseModel):
    question_id: str
    category: str
    question_text: str
    answer: str
    score: Optional[float]
    notes: Optional[str] = None
    guidance: Optional[str] = None
    evidence_required: Optional[str] = None
    risk_severity: Optional[str] = None
    recommendation: Optional[str] = None

class AssessmentResult(BaseModel):
    id: int
    business_id: int
    application_id: int
    name: str
    industry: Optional[str] = None
    question_version: Optional[str] = "2.0"
    overall_score: float
    fairness_score: float
    transparency_score: float
    privacy_score: float
    sustainability_score: float
    dimension_scores: List[DimensionScore]
    completed_at: datetime.datetime
    disclaimer: str = "Self-reported SME governance assessment; does not constitute statutory certification or legal compliance guarantee."
    responses: Optional[List[AssessmentResponseDetail]] = None

    class Config:
        from_attributes = True

# --- Dataset Manager ---
class DatasetResponse(BaseModel):
    id: int
    application_id: Optional[int]
    filename: str
    original_filename: str
    file_size_bytes: int
    row_count: int
    column_count: int
    checksum: str
    schema_version: str
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class DatasetPreview(BaseModel):
    dataset_id: int
    filename: str
    row_count: int
    column_count: int
    columns: List[str]
    dtypes: Dict[str, str]
    head: List[Dict[str, Any]]
    missing_counts: Dict[str, int]
    duplicate_count: int

class CleanDataRequest(BaseModel):
    drop_duplicates: bool = True
    fill_missing_numeric: str = "median"  # "mean", "median", "drop"
    fill_missing_categorical: str = "mode"  # "mode", "unknown", "drop"
    remove_outliers: bool = False

# --- Fairness & Bias ---
class FairnessAnalyzeRequest(BaseModel):
    application_id: int
    dataset_id: Optional[int] = None
    sensitive_attribute: str
    target_attribute: str
    favorable_outcome: Any  # e.g., 1 or "Selected" or "Yes"

class GroupMetric(BaseModel):
    group: str
    total_count: int
    positive_count: int
    selection_rate: float
    tpr: Optional[float] = None
    fpr: Optional[float] = None
    tnr: Optional[float] = None
    fnr: Optional[float] = None

class FairnessAnalysisResponse(BaseModel):
    sensitive_attribute: str
    target_attribute: str
    favorable_outcome: str
    total_samples: int
    groups: List[str]
    group_metrics: List[GroupMetric]
    demographic_parity_diff: float
    demographic_parity_ratio: float
    equal_opportunity_diff: Optional[float]
    four_fifths_rule_passed: bool
    risk_level: str  # "Critical", "High", "Medium", "Low"
    recommendations: List[str]
    limitations: List[str]

# --- Explainability ---
class XAIAnalyzeRequest(BaseModel):
    application_id: int
    dataset_id: Optional[int] = None
    target_attribute: Optional[str] = None
    model_type: str = "RandomForest"

class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
    description: str

class SampleExplanation(BaseModel):
    sample_id: int
    features: Dict[str, Any]
    prediction: Any
    probability: float
    model_confidence: Optional[float] = None
    top_positive_features: List[Dict[str, Any]]
    top_negative_features: List[Dict[str, Any]]
    plain_narrative: str

class XAIAnalysisResponse(BaseModel):
    model_name: str
    task_type: str
    model_accuracy: float
    accuracy_warning: Optional[str] = None
    prediction_disclaimer: Optional[str] = None
    global_importance: List[FeatureImportanceItem]
    sample_explanations: List[SampleExplanation]
    methodology: str
    correlation_causation_caveat: str

# --- Privacy Guard ---
class PrivacyScanRequest(BaseModel):
    application_id: int
    dataset_id: Optional[int] = None

class PIIFindingItem(BaseModel):
    column: str
    pii_type: str  # "Email", "Phone", "SSN/National ID", "Credit Card", "Full Name / Identifier"
    sample_masked: str
    match_count: int
    risk_severity: str

class PrivacyScanResponse(BaseModel):
    total_records_scanned: int
    pii_detected_count: int
    findings: List[PIIFindingItem]
    missing_summary: Dict[str, int]
    duplicate_rows: int
    data_minimization_alerts: List[str]
    governance_checklist_status: Dict[str, str]
    risk_level: str
    disclaimer: str

# --- Green AI Monitor ---
class SustainabilityCalculateRequest(BaseModel):
    application_id: int
    compute_duration_hours: float
    power_draw_kw: float
    emission_factor_kg_per_kwh: Optional[float] = None
    region_preset: Optional[str] = "us-east-grid"

class OptimizationScenario(BaseModel):
    scenario_name: str
    description: str
    projected_energy_kwh: float
    projected_co2e_kg: float
    reduction_percentage: float
    annual_cost_savings_estimate_usd: float

class SustainabilityResponse(BaseModel):
    compute_duration_hours: float
    power_draw_kw: float
    energy_kwh: float
    emission_factor_kg_per_kwh: float
    region_name: str
    estimated_co2e_kg: float
    equivalent_car_miles: float
    tree_seedlings_needed_10_years: float
    scenarios: List[OptimizationScenario]
    actionable_recommendations: List[str]
    assumptions_disclaimer: str

# --- Risk Center ---
class RiskItem(BaseModel):
    id: int
    application_id: int
    assessment_id: Optional[int] = None
    title: str
    description: str
    source_module: str
    severity: str
    evidence: str
    business_impact: str
    recommended_action: str
    status: str
    risk_key: Optional[str] = None
    category: Optional[str] = None
    likelihood: Optional[str] = "Medium"
    impact: Optional[str] = "Medium"
    exposure_factor: Optional[str] = "Medium"
    control_effectiveness: Optional[str] = "Weak"
    risk_score: Optional[float] = 50.0
    evidence_source: Optional[str] = "Self-reported / Unverified"
    is_verified: Optional[bool] = False
    lifecycle_status: Optional[str] = "New"
    responsible_owner: Optional[str] = None
    target_date: Optional[str] = None
    completion_notes: Optional[str] = None
    supporting_evidence: Optional[str] = None
    remediation_history_json: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class RiskCreate(BaseModel):
    application_id: int
    assessment_id: Optional[int] = None
    title: str
    description: str
    source_module: str
    severity: str
    evidence: str
    business_impact: str
    recommended_action: str
    status: str = "Open"
    risk_key: Optional[str] = None
    category: Optional[str] = None
    likelihood: Optional[str] = "Medium"
    impact: Optional[str] = "Medium"
    exposure_factor: Optional[str] = "Medium"
    control_effectiveness: Optional[str] = "Weak"
    risk_score: Optional[float] = 50.0
    evidence_source: Optional[str] = "Self-reported / Unverified"
    is_verified: Optional[bool] = False
    lifecycle_status: Optional[str] = "New"
    responsible_owner: Optional[str] = None
    target_date: Optional[str] = None
    completion_notes: Optional[str] = None
    supporting_evidence: Optional[str] = None

class RiskUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    recommended_action: Optional[str] = None
    responsible_owner: Optional[str] = None
    target_date: Optional[str] = None
    completion_notes: Optional[str] = None
    supporting_evidence: Optional[str] = None
    is_verified: Optional[bool] = None

# --- Recommendations ---
class RecommendationItem(BaseModel):
    id: int
    application_id: int
    problem: str
    why_it_matters: str
    action: str
    priority: str
    expected_business_benefit: str
    responsible_team: str
    status: str
    source_module: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Dashboard ---
class DashboardSummary(BaseModel):
    business: Optional[BusinessResponse]
    application: Optional[AIApplicationResponse]
    overall_governance_score: float
    fairness_score: float
    transparency_score: float
    privacy_score: float
    sustainability_score: float
    total_risks_count: int
    high_critical_risks_count: int
    resolved_risks_count: int
    radar_data: List[Dict[str, Any]]
    risk_distribution: Dict[str, int]
    recent_assessments: List[Dict[str, Any]]
    top_recommendations: List[RecommendationItem]
    recent_alerts: List[Dict[str, Any]]
    green_co2e_summary_kg: float
