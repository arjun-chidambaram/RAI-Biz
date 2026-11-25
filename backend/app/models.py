import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True, default="")
    role = Column(String(50), default="Compliance Officer")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    sessions = relationship("SessionRecord", back_populates="user", cascade="all, delete-orphan")
    business_memberships = relationship("BusinessUser", back_populates="user", cascade="all, delete-orphan")

class EmailOTP(Base):
    __tablename__ = "email_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    otp_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SessionRecord(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_hash = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="sessions")

class BusinessUser(Base):
    __tablename__ = "business_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    role = Column(String(50), default="Owner")  # "Owner", "Admin", "Member", "Viewer"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="business_memberships")
    business = relationship("Business", back_populates="user_memberships")

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    industry = Column(String(100), nullable=False)
    size = Column(String(50), nullable=False)  # e.g., "1-10", "11-50", "51-250"
    location = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    applications = relationship("AIApplication", back_populates="business", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="business")
    user_memberships = relationship("BusinessUser", back_populates="business", cascade="all, delete-orphan")

class AIApplication(Base):
    __tablename__ = "ai_applications"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    name = Column(String(255), index=True, nullable=False)
    purpose = Column(Text, nullable=False)
    business_function = Column(String(100), nullable=False)  # e.g., "Recruitment", "Credit Scoring", "Customer Support"
    data_types = Column(String(255), nullable=False)  # e.g., "Resumes, Candidate Ratings, Test Scores"
    automated_decision_impact = Column(String(50), default="High")  # "High", "Medium", "Low"
    human_oversight = Column(String(50), default="None")  # "Full", "Partial", "None"
    model_type = Column(String(100), default="Classification Model")
    affected_stakeholders = Column(String(255), nullable=True)
    external_services = Column(String(255), nullable=True)
    infrastructure_type = Column(String(100), nullable=True)
    status = Column(String(50), default="Active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    business = relationship("Business", back_populates="applications")
    assessments = relationship("Assessment", back_populates="application", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="application")
    risks = relationship("Risk", back_populates="application", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="application", cascade="all, delete-orphan")

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    application_id = Column(Integer, ForeignKey("ai_applications.id"), nullable=False)
    industry = Column(String(100), nullable=True)
    question_version = Column(String(50), default="2.0")
    question_set_json = Column(Text, nullable=True)
    name = Column(String(255), nullable=False)
    overall_score = Column(Float, default=0.0)
    fairness_score = Column(Float, default=0.0)
    transparency_score = Column(Float, default=0.0)
    privacy_score = Column(Float, default=0.0)
    sustainability_score = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    is_current = Column(Boolean, default=True)
    completed_at = Column(DateTime, default=datetime.datetime.utcnow)

    business = relationship("Business", back_populates="assessments")
    application = relationship("AIApplication", back_populates="assessments")
    responses = relationship("AssessmentResponse", back_populates="assessment", cascade="all, delete-orphan")

class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    question_id = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)  # "fairness", "transparency", "privacy", "sustainability"
    question_text = Column(Text, nullable=False)
    guidance = Column(Text, nullable=True)
    evidence_required = Column(Text, nullable=True)
    risk_severity = Column(String(50), nullable=True)
    recommendation_text = Column(Text, nullable=True)
    answer = Column(String(20), nullable=False)  # "Yes", "Partially", "No", "N/A"
    score = Column(Float, nullable=True)  # 100, 50, 0, or None if N/A
    notes = Column(Text, nullable=True)

    assessment = relationship("Assessment", back_populates="responses")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("ai_applications.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    checksum = Column(String(64), nullable=False)  # SHA-256
    schema_json = Column(Text, nullable=True)
    schema_version = Column(String(50), default="1.0")
    status = Column(String(50), default="Uploaded")  # "Uploaded", "Validated", "Cleaned"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    application = relationship("AIApplication", back_populates="datasets")
    records = relationship("DatasetRecord", back_populates="dataset", cascade="all, delete-orphan")

class DatasetRecord(Base):
    __tablename__ = "dataset_records"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    record_type = Column(String(50), default="sample")  # "sample", "rejected"
    row_index = Column(Integer, nullable=False)
    raw_data_json = Column(Text, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dataset = relationship("Dataset", back_populates="records")

class FairnessResult(Base):
    __tablename__ = "fairness_results"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("ai_applications.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    sensitive_attribute = Column(String(100), nullable=False)
    target_attribute = Column(String(100), nullable=False)
    favorable_outcome = Column(String(50), nullable=False)
    demographic_parity_diff = Column(Float, default=0.0)
    demographic_parity_ratio = Column(Float, default=0.0)
    equal_opportunity_diff = Column(Float, nullable=True)
    group_metrics_json = Column(Text, nullable=False)
    confusion_matrices_json = Column(Text, nullable=True)
    risk_level = Column(String(20), default="Low")  # "Critical", "High", "Medium", "Low"
    recommendations_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ExplainabilityResult(Base):
    __tablename__ = "explainability_results"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("ai_applications.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    model_name = Column(String(100), default="RandomForestClassifier")
    task_type = Column(String(50), default="Recruitment Qualification")
    global_importance_json = Column(Text, nullable=False)
    sample_explanations_json = Column(Text, nullable=True)
    summary_narrative = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PrivacyFinding(Base):
    __tablename__ = "privacy_findings"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("ai_applications.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    total_records_scanned = Column(Integer, default=0)
    pii_detected_count = Column(Integer, default=0)
    findings_json = Column(Text, nullable=False)
    missing_duplicate_stats_json = Column(Text, nullable=True)
    data_minimization_alerts_json = Column(Text, nullable=True)
    risk_level = Column(String(20), default="Low")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SustainabilityResult(Base):
    __tablename__ = "sustainability_results"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("ai_applications.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    compute_duration_hours = Column(Float, default=0.0)
    power_draw_kw = Column(Float, default=0.0)
    energy_kwh = Column(Float, default=0.0)
    emission_factor = Column(Float, default=0.0)
    estimated_co2e_kg = Column(Float, default=0.0)
    region_name = Column(String(100), default="Global Average")
    optimization_scenarios_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Risk(Base):
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("ai_applications.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    source_module = Column(String(50), nullable=False)  # "fairness", "transparency", "privacy", "governance", "sustainability", "assessment"
    severity = Column(String(20), nullable=False)  # "Critical", "High", "Medium", "Low"
    evidence = Column(Text, nullable=False)
    business_impact = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    status = Column(String(30), default="Open")  # "Open", "In progress", "Resolved"
    risk_key = Column(String(100), nullable=True, index=True)
    category = Column(String(50), nullable=True)
    likelihood = Column(String(20), default="Medium")
    impact = Column(String(20), default="Medium")
    exposure_factor = Column(String(100), default="Medium")
    control_effectiveness = Column(String(100), default="Weak")
    risk_score = Column(Float, default=50.0)
    evidence_source = Column(String(100), default="Self-reported assessment answer")
    is_verified = Column(Boolean, default=False)
    lifecycle_status = Column(String(50), default="New")  # "New", "Repeated", "Improved", "Resolved", "Reopened"
    responsible_owner = Column(String(100), nullable=True)
    target_date = Column(String(50), nullable=True)
    completion_notes = Column(Text, nullable=True)
    supporting_evidence = Column(Text, nullable=True)
    remediation_history_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    application = relationship("AIApplication", back_populates="risks")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("ai_applications.id"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    problem = Column(String(255), nullable=False)
    why_it_matters = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    priority = Column(String(20), default="High")  # "High", "Medium", "Low"
    expected_business_benefit = Column(Text, nullable=False)
    responsible_team = Column(String(100), default="Engineering")  # "Engineering", "Legal & Compliance", "HR & Operations", "Executive Leadership"
    status = Column(String(30), default="Pending")  # "Pending", "Implemented"
    source_module = Column(String(50), default="assessment")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    application = relationship("AIApplication", back_populates="recommendations")

class IngestionLog(Base):
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
