import os
import json
import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import pandas as pd

from .database import engine, Base, get_db
from .config import settings
from .models import (
    User, Business, BusinessUser, AIApplication, Assessment, AssessmentResponse,
    Dataset, DatasetRecord, Risk, Recommendation, FairnessResult,
    ExplainabilityResult, PrivacyFinding, SustainabilityResult
)
from .schemas import (
    BusinessCreate, BusinessResponse,
    AIApplicationBase, AIApplicationCreate, AIApplicationResponse,
    ProfileUpdatePayload, ProfileUpdateResponse,
    QuestionDefinition, GenerateQuestionsRequest, DynamicQuestionSetResponse,
    AssessmentCreate, AssessmentResult, AssessmentResponseDetail, DimensionScore,
    DatasetResponse, DatasetPreview, CleanDataRequest,
    FairnessAnalyzeRequest, FairnessAnalysisResponse,
    XAIAnalyzeRequest, XAIAnalysisResponse,
    PrivacyScanRequest, PrivacyScanResponse,
    SustainabilityCalculateRequest, SustainabilityResponse,
    RiskItem, RiskCreate, RiskUpdate,
    RecommendationItem, DashboardSummary
)
from .services.assessment_service import get_questions, process_and_save_assessment, score_assessment
from .services.dynamic_assessment_engine import generate_industry_assessment, detect_industry_key, get_supported_industries
from .services.fairness_service import analyze_fairness, record_fairness_findings
from .services.xai_service import train_and_explain_model, record_explainability_findings
from .services.privacy_service import scan_dataframe_privacy, record_privacy_findings
from .services.green_ai_service import calculate_sustainability_metrics, record_sustainability_findings, REGION_EMISSION_FACTORS
from .services.dataset_service import save_and_ingest_dataset, get_dataset_preview, clean_dataset
from .services.storage_service import load_dataset_dataframe, resolve_dataset_path, DatasetFileNotFoundError
from .services.risk_service import get_risks, create_risk, update_risk
from .services.risk_intelligence_engine import RiskIntelligenceEngine, UniversalRiskEngine
from .services.recommendation_service import generate_and_save_recommendations
from .services.pdf_service import generate_assessment_pdf
from .services.demo_seed_service import seed_demo_data
from .services.auth_service import get_user_primary_business, get_user_primary_application
from .routers.auth import router as auth_router, require_current_user, get_current_user, verify_csrf

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RAI-Biz API",
    description="An AI-Powered Responsible AI Governance, Risk Assessment and Optimization Platform for SMEs.",
    version="1.0.0"
)

# CORS configuration supporting credentials (cookies)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    origins.extend([o.strip() for o in cors_origins_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount authentication router
app.include_router(auth_router)

# Health check endpoints for deployment monitoring
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    db_dialect = "unknown"
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_dialect = db.bind.dialect.name
    except Exception:
        db_status = "error"
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "RAI-Biz API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "database_engine": db_dialect,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.on_event("startup")
def startup_event():
    # Ensure upload & data directories exist
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Automatically seed initial demo data if database is empty
    db = next(get_db())
    try:
        if db.query(Business).count() == 0:
            seed_demo_data(db)
    finally:
        db.close()

# ----------------- TENANT AUTHORIZATION HELPERS -----------------
def get_user_accessible_business_ids(user: User, db: Session, include_demo: bool = True) -> List[int]:
    """Returns business IDs accessible to the current user (user's businesses + shared demo)."""
    memberships = db.query(BusinessUser).filter(BusinessUser.user_id == user.id).all()
    b_ids = [m.business_id for m in memberships]
    if include_demo and 1 not in b_ids:
        demo_biz = db.query(Business).filter(Business.id == 1).first()
        if demo_biz:
            b_ids.append(1)
    return b_ids

def verify_business_access(user: User, business_id: int, db: Session, include_demo: bool = True):
    """Enforces tenant boundary: user cannot access another user's private business."""
    accessible = get_user_accessible_business_ids(user, db, include_demo=include_demo)
    if business_id not in accessible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access records for this business."
        )

def verify_application_access(user: User, application_id: int, db: Session, include_demo: bool = True) -> AIApplication:
    """Verifies user can access the application and returns the model."""
    app_obj = db.query(AIApplication).filter(AIApplication.id == application_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="AI Application not found")
    verify_business_access(user, app_obj.business_id, db, include_demo=include_demo)
    return app_obj

# ----------------- BUSINESS & APPLICATION -----------------
@app.get("/api/businesses/profile", response_model=ProfileUpdateResponse, tags=["Business"])
def get_business_profile_endpoint(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    biz = get_user_primary_business(db, current_user.id)
    if not biz:
        raise HTTPException(status_code=404, detail="No business profile found")
    app_obj = get_user_primary_application(db, current_user.id)
    if not app_obj:
        app_obj = db.query(AIApplication).filter(AIApplication.business_id == biz.id).order_by(AIApplication.id.desc()).first()
    return ProfileUpdateResponse(
        success=True,
        business=BusinessResponse.from_orm(biz),
        application=AIApplicationResponse.from_orm(app_obj) if app_obj else None,
        message="Profile retrieved successfully."
    )

@app.put("/api/businesses/profile", response_model=ProfileUpdateResponse, tags=["Business"])
def update_business_profile_endpoint(
    payload: ProfileUpdatePayload,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves or updates the authenticated user's active business and target AI application.
    Ensures persistence and synchronization across Overview Dashboard and modules.
    """
    biz = get_user_primary_business(db, current_user.id)
    if biz and biz.id != 1:
        # Update existing user business in-place
        biz.name = payload.name
        biz.industry = payload.industry
        biz.size = payload.size
        biz.location = payload.location
        biz.description = payload.description
        biz.contact_email = payload.contact_email
        biz.updated_at = datetime.datetime.utcnow()
    else:
        # Create new business and associate membership
        biz = Business(
            name=payload.name,
            industry=payload.industry,
            size=payload.size,
            location=payload.location,
            description=payload.description,
            contact_email=payload.contact_email
        )
        db.add(biz)
        db.commit()
        db.refresh(biz)
        db.add(BusinessUser(user_id=current_user.id, business_id=biz.id, role="Owner"))
        db.commit()

    # Update or create AI application for this business
    app_obj = db.query(AIApplication).filter(AIApplication.business_id == biz.id).order_by(AIApplication.id.desc()).first()
    if app_obj and app_obj.id != 1:
        app_obj.name = payload.app_name
        app_obj.purpose = payload.purpose
        app_obj.business_function = payload.business_function
        app_obj.data_types = payload.data_types
        app_obj.automated_decision_impact = payload.automated_decision_impact
        app_obj.human_oversight = payload.human_oversight
        if getattr(payload, "affected_stakeholders", None):
            app_obj.affected_stakeholders = payload.affected_stakeholders
        if getattr(payload, "external_services", None):
            app_obj.external_services = payload.external_services
        if getattr(payload, "infrastructure_type", None):
            app_obj.infrastructure_type = payload.infrastructure_type
        app_obj.updated_at = datetime.datetime.utcnow()
    else:
        app_obj = AIApplication(
            business_id=biz.id,
            name=payload.app_name,
            purpose=payload.purpose,
            business_function=payload.business_function,
            data_types=payload.data_types,
            automated_decision_impact=payload.automated_decision_impact,
            human_oversight=payload.human_oversight,
            affected_stakeholders=getattr(payload, "affected_stakeholders", "Not Provided"),
            external_services=getattr(payload, "external_services", "Not Provided"),
            infrastructure_type=getattr(payload, "infrastructure_type", "Unknown"),
            status="Active"
        )
        db.add(app_obj)

    db.commit()
    db.refresh(biz)
    db.refresh(app_obj)

    return ProfileUpdateResponse(
        success=True,
        business=BusinessResponse.from_orm(biz),
        application=AIApplicationResponse.from_orm(app_obj),
        message="Business profile and AI application updated successfully."
    )

@app.post("/api/businesses", response_model=BusinessResponse, tags=["Business"])
def create_business_endpoint(
    biz: BusinessCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    db_biz = Business(**biz.model_dump())
    db.add(db_biz)
    db.commit()
    db.refresh(db_biz)

    # Automatically associate the business with the current user
    membership = BusinessUser(
        user_id=current_user.id,
        business_id=db_biz.id,
        role="Owner"
    )
    db.add(membership)
    db.commit()

    return db_biz

@app.put("/api/businesses/{id}", response_model=BusinessResponse, tags=["Business"])
def update_business_endpoint(
    id: int,
    biz_in: BusinessCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    verify_business_access(current_user, id, db, include_demo=False)
    biz = db.query(Business).filter(Business.id == id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
    for key, val in biz_in.model_dump().items():
        setattr(biz, key, val)
    biz.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(biz)
    return biz

@app.get("/api/businesses", response_model=List[BusinessResponse], tags=["Business"])
def list_businesses(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    accessible_ids = get_user_accessible_business_ids(current_user, db, include_demo=True)
    return db.query(Business).filter(Business.id.in_(accessible_ids)).order_by(Business.id.desc()).all()

@app.post("/api/applications", response_model=AIApplicationResponse, tags=["AI Applications"])
def create_application_endpoint(
    app_in: AIApplicationCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    verify_business_access(current_user, app_in.business_id, db, include_demo=False)
    biz = db.query(Business).filter(Business.id == app_in.business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
    db_app = AIApplication(**app_in.model_dump())
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

@app.put("/api/applications/{id}", response_model=AIApplicationResponse, tags=["AI Applications"])
def update_application_endpoint(
    id: int,
    app_in: AIApplicationBase,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    app_obj = verify_application_access(current_user, id, db, include_demo=False)
    for key, val in app_in.model_dump().items():
        setattr(app_obj, key, val)
    app_obj.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(app_obj)
    return app_obj

@app.get("/api/applications", response_model=List[AIApplicationResponse], tags=["AI Applications"])
def list_applications(
    business_id: Optional[int] = None,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    accessible_ids = get_user_accessible_business_ids(current_user, db, include_demo=True)
    if business_id:
        verify_business_access(current_user, business_id, db, include_demo=True)
        return db.query(AIApplication).filter(AIApplication.business_id == business_id).order_by(AIApplication.id.desc()).all()
    return db.query(AIApplication).filter(AIApplication.business_id.in_(accessible_ids)).order_by(AIApplication.id.desc()).all()

# ----------------- MODULE 1: ASSESSMENT -----------------
@app.get("/api/assessments/industries", tags=["Assessment"])
def get_supported_industries_endpoint():
    return get_supported_industries()

@app.get("/api/assessments/questions", response_model=List[QuestionDefinition], tags=["Assessment"])
def get_assessment_questions(
    application_id: Optional[int] = Query(None),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    app_obj = None
    if application_id:
        verify_application_access(current_user, application_id, db, include_demo=True)
        app_obj = db.query(AIApplication).filter(AIApplication.id == application_id).first()
    else:
        app_obj = get_user_primary_application(db, current_user.id)
        if not app_obj:
            user_primary_biz = get_user_primary_business(db, current_user.id)
            if user_primary_biz:
                app_obj = db.query(AIApplication).filter(AIApplication.business_id == user_primary_biz.id).order_by(AIApplication.id.desc()).first()

    if app_obj:
        biz_obj = db.query(Business).filter(Business.id == app_obj.business_id).first()
        if biz_obj:
            return get_questions(business=biz_obj, application=app_obj)

    return get_questions()

@app.post("/api/assessments/generate-questions", response_model=DynamicQuestionSetResponse, tags=["Assessment"])
def generate_assessment_questions_endpoint(
    req: GenerateQuestionsRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    target_app_id = req.application_id
    app_obj = None

    if target_app_id:
        verify_application_access(current_user, target_app_id, db, include_demo=True)
        app_obj = db.query(AIApplication).filter(AIApplication.id == target_app_id).first()
    else:
        # Fall back to user's primary active AI application
        app_obj = get_user_primary_application(db, current_user.id)
        if not app_obj:
            user_primary_biz = get_user_primary_business(db, current_user.id)
            if user_primary_biz:
                app_obj = db.query(AIApplication).filter(AIApplication.business_id == user_primary_biz.id).order_by(AIApplication.id.desc()).first()

    if not app_obj:
        raise HTTPException(status_code=404, detail="AI Application not found for this user account.")

    biz_obj = db.query(Business).filter(Business.id == app_obj.business_id).first()
    if not biz_obj:
        raise HTTPException(status_code=404, detail="Business profile not found for this AI application.")

    try:
        questions = generate_industry_assessment(biz_obj, app_obj, force_llm=bool(req.force_llm))
    except Exception as e:
        # Failsafe fallback to standard catalog
        questions = get_questions(business=biz_obj, application=app_obj)

    ind_key = detect_industry_key(biz_obj.industry, app_obj.business_function)
    gen_source = "gemini_llm" if (req.force_llm and bool(settings.GEMINI_API_KEY)) else "curated_domain_engine"

    return DynamicQuestionSetResponse(
        business_id=biz_obj.id,
        application_id=app_obj.id,
        business_name=biz_obj.name,
        application_name=app_obj.name,
        industry=biz_obj.industry or "General SME",
        industry_key=ind_key,
        generation_source=gen_source,
        dimensions=["fairness", "transparency", "privacy", "sustainability"],
        question_count=len(questions),
        questions=questions
    )

@app.post("/api/assessments", response_model=AssessmentResult, tags=["Assessment"])
def submit_assessment(
    data: AssessmentCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    app_obj = verify_application_access(current_user, data.application_id, db, include_demo=True)
    
    assessment = process_and_save_assessment(db, data, user_id=current_user.id)
    
    # Automatically evaluate risks and contextual recommendations via Centralized Risk Intelligence Engine
    try:
        RiskIntelligenceEngine.evaluate_and_sync(
            db=db,
            application_id=app_obj.id,
            assessment_id=assessment.id,
            actor_email=current_user.email
        )
    except Exception:
        generate_and_save_recommendations(db, application_id=app_obj.id, assessment_id=assessment.id)

    dim_scores = [
        DimensionScore(dimension="Fairness", score=assessment.fairness_score, status="Compliant" if assessment.fairness_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
        DimensionScore(dimension="Transparency", score=assessment.transparency_score, status="Compliant" if assessment.transparency_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
        DimensionScore(dimension="Privacy", score=assessment.privacy_score, status="Compliant" if assessment.privacy_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
        DimensionScore(dimension="Sustainability", score=assessment.sustainability_score, status="Compliant" if assessment.sustainability_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
    ]

    responses = [
        AssessmentResponseDetail(
            question_id=r.question_id,
            category=r.category,
            question_text=r.question_text,
            guidance=r.guidance,
            evidence_required=r.evidence_required,
            risk_severity=r.risk_severity,
            recommendation_text=r.recommendation_text,
            answer=r.answer,
            score=r.score,
            notes=r.notes
        )
        for r in assessment.responses
    ]

    return AssessmentResult(
        id=assessment.id,
        business_id=assessment.business_id,
        application_id=assessment.application_id,
        user_id=assessment.user_id,
        industry=assessment.industry,
        question_version=assessment.question_version,
        name=assessment.name,
        overall_score=assessment.overall_score,
        fairness_score=assessment.fairness_score,
        transparency_score=assessment.transparency_score,
        privacy_score=assessment.privacy_score,
        sustainability_score=assessment.sustainability_score,
        dimension_scores=dim_scores,
        completed_at=assessment.completed_at,
        responses=responses
    )

@app.get("/api/assessments", response_model=List[AssessmentResult], tags=["Assessment"])
def list_assessments(
    application_id: Optional[int] = None,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    accessible_bids = get_user_accessible_business_ids(current_user, db, include_demo=True)
    accessible_apps = db.query(AIApplication.id).filter(AIApplication.business_id.in_(accessible_bids)).all()
    accessible_app_ids = [a[0] for a in accessible_apps]

    query = db.query(Assessment).filter(Assessment.application_id.in_(accessible_app_ids))
    if application_id:
        verify_application_access(current_user, application_id, db, include_demo=True)
        query = query.filter(Assessment.application_id == application_id)
        
    assessments = query.order_by(Assessment.completed_at.desc()).all()

    results = []
    for a in assessments:
        dim_scores = [
            DimensionScore(dimension="Fairness", score=a.fairness_score, status="Compliant" if a.fairness_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
            DimensionScore(dimension="Transparency", score=a.transparency_score, status="Compliant" if a.transparency_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
            DimensionScore(dimension="Privacy", score=a.privacy_score, status="Compliant" if a.privacy_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
            DimensionScore(dimension="Sustainability", score=a.sustainability_score, status="Compliant" if a.sustainability_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
        ]
        results.append(AssessmentResult(
            id=a.id,
            business_id=a.business_id,
            application_id=a.application_id,
            user_id=a.user_id,
            industry=a.industry,
            question_version=a.question_version,
            name=a.name,
            overall_score=a.overall_score,
            fairness_score=a.fairness_score,
            transparency_score=a.transparency_score,
            privacy_score=a.privacy_score,
            sustainability_score=a.sustainability_score,
            dimension_scores=dim_scores,
            completed_at=a.completed_at
        ))
    return results

@app.get("/api/assessments/{id}", response_model=AssessmentResult, tags=["Assessment"])
def get_assessment(
    id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    a = db.query(Assessment).filter(Assessment.id == id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")

    verify_business_access(current_user, a.business_id, db, include_demo=True)

    dim_scores = [
        DimensionScore(dimension="Fairness", score=a.fairness_score, status="Compliant" if a.fairness_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
        DimensionScore(dimension="Transparency", score=a.transparency_score, status="Compliant" if a.transparency_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
        DimensionScore(dimension="Privacy", score=a.privacy_score, status="Compliant" if a.privacy_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
        DimensionScore(dimension="Sustainability", score=a.sustainability_score, status="Compliant" if a.sustainability_score >= 80 else "Attention Needed", answered_count=5, total_count=5),
    ]
    responses = [
        AssessmentResponseDetail(
            question_id=r.question_id,
            category=r.category,
            question_text=r.question_text,
            guidance=r.guidance,
            evidence_required=r.evidence_required,
            risk_severity=r.risk_severity,
            recommendation_text=r.recommendation_text,
            answer=r.answer,
            score=r.score,
            notes=r.notes
        )
        for r in a.responses
    ]
    return AssessmentResult(
        id=a.id,
        business_id=a.business_id,
        application_id=a.application_id,
        user_id=a.user_id,
        industry=a.industry,
        question_version=a.question_version,
        name=a.name,
        overall_score=a.overall_score,
        fairness_score=a.fairness_score,
        transparency_score=a.transparency_score,
        privacy_score=a.privacy_score,
        sustainability_score=a.sustainability_score,
        dimension_scores=dim_scores,
        completed_at=a.completed_at,
        responses=responses
    )

# ----------------- DATASET MANAGER -----------------
@app.post("/api/datasets/upload", response_model=DatasetResponse, tags=["Dataset Manager"])
async def upload_dataset(
    file: UploadFile = File(...),
    application_id: Optional[int] = Form(None),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    if application_id:
        verify_application_access(current_user, application_id, db, include_demo=True)

    filename = file.filename or "uploaded_data.csv"
    ext = filename.lower().split(".")[-1]
    if ext not in ["csv", "json"]:
        raise HTTPException(status_code=400, detail="Only CSV and JSON file formats are supported.")

    file_bytes = await file.read()
    if len(file_bytes) > 25 * 1024 * 1024:  # 25MB limit
        raise HTTPException(status_code=400, detail="File size exceeds maximum 25MB limit.")

    dataset = save_and_ingest_dataset(db, file_bytes, filename, application_id)
    return dataset

@app.get("/api/datasets", response_model=List[DatasetResponse], tags=["Dataset Manager"])
def list_datasets(
    application_id: Optional[int] = None,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    accessible_bids = get_user_accessible_business_ids(current_user, db, include_demo=True)
    accessible_apps = db.query(AIApplication.id).filter(AIApplication.business_id.in_(accessible_bids)).all()
    accessible_app_ids = [a[0] for a in accessible_apps]

    query = db.query(Dataset).filter(
        (Dataset.application_id.in_(accessible_app_ids)) | (Dataset.application_id == None)
    )
    if application_id:
        verify_application_access(current_user, application_id, db, include_demo=True)
        query = query.filter(Dataset.application_id == application_id)

    return query.order_by(Dataset.created_at.desc()).all()

@app.get("/api/datasets/{id}", response_model=DatasetResponse, tags=["Dataset Manager"])
def get_dataset(
    id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    d = db.query(Dataset).filter(Dataset.id == id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if d.application_id:
        verify_application_access(current_user, d.application_id, db, include_demo=True)
    return d

@app.get("/api/datasets/{id}/preview", response_model=DatasetPreview, tags=["Dataset Manager"])
def dataset_preview_endpoint(
    id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    d = db.query(Dataset).filter(Dataset.id == id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if d.application_id:
        verify_application_access(current_user, d.application_id, db, include_demo=True)

    try:
        return get_dataset_preview(db, id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/datasets/{id}/clean", response_model=DatasetResponse, tags=["Dataset Manager"])
def clean_dataset_endpoint(
    id: int,
    req: CleanDataRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    d = db.query(Dataset).filter(Dataset.id == id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if d.application_id:
        verify_application_access(current_user, d.application_id, db, include_demo=True)

    try:
        cleaned_ds, clean_count, rejected_count = clean_dataset(
            db, id,
            drop_duplicates=req.drop_duplicates,
            fill_missing_numeric=req.fill_missing_numeric,
            fill_missing_categorical=req.fill_missing_categorical
        )
        return cleaned_ds
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/datasets/{id}/export-rejected", tags=["Dataset Manager"])
def export_rejected_records(
    id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    d = db.query(Dataset).filter(Dataset.id == id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if d.application_id:
        verify_application_access(current_user, d.application_id, db, include_demo=True)

    records = db.query(DatasetRecord).filter(
        DatasetRecord.dataset_id == id,
        DatasetRecord.record_type == "rejected"
    ).all()
    
    if not records:
        return {"rejected_count": 0, "records": []}

    output = []
    for r in records:
        row_data = json.loads(r.raw_data_json)
        row_data["_rejection_reason"] = r.rejection_reason
        row_data["_row_index"] = r.row_index
        output.append(row_data)

    return {"rejected_count": len(output), "records": output}

# ----------------- MODULE 2: FAIRNESS & BIAS -----------------
@app.post("/api/fairness/analyze", response_model=FairnessAnalysisResponse, tags=["Fairness"])
def analyze_fairness_endpoint(
    req: FairnessAnalyzeRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    verify_application_access(current_user, req.application_id, db, include_demo=True)

    if req.dataset_id:
        ds = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if ds.application_id and ds.application_id != req.application_id and req.application_id != 1:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset '{ds.original_filename or ds.filename}' is not associated with this application."
            )
    else:
        ds = db.query(Dataset).filter(Dataset.application_id == req.application_id).order_by(Dataset.id.desc()).first()
        if not ds:
            raise HTTPException(status_code=404, detail="No dataset found for this application")

    df = load_dataset_dataframe(ds)

    try:
        res = analyze_fairness(
            df=df,
            sensitive_column=req.sensitive_attribute,
            target_column=req.target_attribute,
            favorable_outcome=req.favorable_outcome
        )
        record_fairness_findings(db, req.application_id, res, ds.id)
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- MODULE 3: EXPLAINABILITY -----------------
@app.post("/api/explainability/analyze", response_model=XAIAnalysisResponse, tags=["Explainability"])
def analyze_explainability_endpoint(
    req: XAIAnalyzeRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    verify_application_access(current_user, req.application_id, db, include_demo=True)

    if req.dataset_id:
        ds = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if ds.application_id and ds.application_id != req.application_id and req.application_id != 1:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset '{ds.original_filename or ds.filename}' is not associated with this application."
            )
    else:
        ds = db.query(Dataset).filter(Dataset.application_id == req.application_id).order_by(Dataset.id.desc()).first()
        if not ds:
            raise HTTPException(status_code=404, detail="No dataset found for this application")

    df = load_dataset_dataframe(ds)

    try:
        res = train_and_explain_model(
            df=df,
            target_column=req.target_attribute,
            model_type=req.model_type
        )
        record_explainability_findings(db, req.application_id, res)
        return res
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Model training and explainability error: {str(e)}")

# ----------------- MODULE 4: PRIVACY GUARD -----------------
@app.post("/api/privacy/scan", response_model=PrivacyScanResponse, tags=["Privacy"])
def scan_privacy_endpoint(
    req: PrivacyScanRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    verify_application_access(current_user, req.application_id, db, include_demo=True)

    if req.dataset_id:
        ds = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if ds.application_id and ds.application_id != req.application_id and req.application_id != 1:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset '{ds.original_filename or ds.filename}' is not associated with this application."
            )
    else:
        ds = db.query(Dataset).filter(Dataset.application_id == req.application_id).order_by(Dataset.id.desc()).first()
        if not ds:
            raise HTTPException(status_code=404, detail="No dataset found for this application")

    df = load_dataset_dataframe(ds)

    try:
        res = scan_dataframe_privacy(df)
        record_privacy_findings(db, req.application_id, res, ds.id)
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- MODULE 5: GREEN AI -----------------
@app.post("/api/sustainability/calculate", response_model=SustainabilityResponse, tags=["Green AI"])
def calculate_sustainability_endpoint(
    req: SustainabilityCalculateRequest,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    verify_application_access(current_user, req.application_id, db, include_demo=True)

    try:
        res = calculate_sustainability_metrics(
            runtime_hours=req.compute_duration_hours,
            power_draw_kw=req.power_draw_kw,
            emission_factor_override=req.emission_factor_kg_per_kwh,
            region_preset=req.region_preset
        )
        record_sustainability_findings(db, req.application_id, res)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/sustainability/regions", tags=["Green AI"])
def list_emission_regions(
    current_user: User = Depends(require_current_user)
):
    return [{"id": k, **v} for k, v in REGION_EMISSION_FACTORS.items()]

# ----------------- CENTRAL RISK CENTER -----------------
@app.get("/api/risks", response_model=List[RiskItem], tags=["Risk Center"])
def list_risks(
    application_id: Optional[int] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    source_module: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    if application_id:
        verify_application_access(current_user, application_id, db, include_demo=True)
    return get_risks(db, application_id, severity, status, source_module)

@app.post("/api/risks", response_model=RiskItem, tags=["Risk Center"])
def add_risk(
    risk_in: RiskCreate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    verify_application_access(current_user, risk_in.application_id, db, include_demo=True)
    return create_risk(db, risk_in, actor_email=current_user.email)

@app.patch("/api/risks/{id}", response_model=RiskItem, tags=["Risk Center"])
def update_risk_endpoint(
    id: int,
    risk_update: RiskUpdate,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    risk = db.query(Risk).filter(Risk.id == id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    verify_application_access(current_user, risk.application_id, db, include_demo=True)

    try:
        return update_risk(db, id, risk_update, actor_email=current_user.email)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# ----------------- AI RECOMMENDATIONS -----------------
@app.post("/api/recommendations/generate", response_model=List[RecommendationItem], tags=["Recommendations"])
def trigger_recommendation_generation(
    application_id: int,
    assessment_id: Optional[int] = None,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    verify_application_access(current_user, application_id, db, include_demo=True)
    try:
        return generate_and_save_recommendations(db, application_id, assessment_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/recommendations", response_model=List[RecommendationItem], tags=["Recommendations"])
def list_recommendations(
    application_id: Optional[int] = None,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    accessible_bids = get_user_accessible_business_ids(current_user, db, include_demo=True)
    accessible_apps = db.query(AIApplication.id).filter(AIApplication.business_id.in_(accessible_bids)).all()
    accessible_app_ids = [a[0] for a in accessible_apps]

    query = db.query(Recommendation).filter(Recommendation.application_id.in_(accessible_app_ids))
    if application_id:
        verify_application_access(current_user, application_id, db, include_demo=True)
        query = query.filter(Recommendation.application_id == application_id)
    return query.order_by(Recommendation.priority.asc(), Recommendation.created_at.desc()).all()

# ----------------- EXECUTIVE DASHBOARD -----------------
@app.get("/api/dashboard", response_model=DashboardSummary, tags=["Dashboard"])
def get_dashboard_summary(
    application_id: Optional[int] = None,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    accessible_bids = get_user_accessible_business_ids(current_user, db, include_demo=True)
    
    if application_id:
        verify_application_access(current_user, application_id, db, include_demo=True)
        app_obj = db.query(AIApplication).filter(AIApplication.id == application_id).first()
    else:
        # Retrieve authenticated user's active application
        app_obj = get_user_primary_application(db, current_user.id)
        if not app_obj:
            user_primary_biz = get_user_primary_business(db, current_user.id)
            if user_primary_biz:
                app_obj = db.query(AIApplication).filter(AIApplication.business_id == user_primary_biz.id).order_by(AIApplication.id.desc()).first()
        if not app_obj:
            app_obj = db.query(AIApplication).filter(AIApplication.business_id.in_(accessible_bids)).order_by(AIApplication.id.desc()).first()

    if not app_obj:
        return DashboardSummary(
            business=None,
            application=None,
            overall_governance_score=0.0,
            fairness_score=0.0,
            transparency_score=0.0,
            privacy_score=0.0,
            sustainability_score=0.0,
            total_risks_count=0,
            high_critical_risks_count=0,
            resolved_risks_count=0,
            radar_data=[],
            risk_distribution={},
            recent_assessments=[],
            top_recommendations=[],
            recent_alerts=[],
            green_co2e_summary_kg=0.0
        )

    business = db.query(Business).filter(Business.id == app_obj.business_id).first()
    curr_assessment = db.query(Assessment).filter(Assessment.application_id == app_obj.id, Assessment.is_current == True).first()
    if not curr_assessment:
        curr_assessment = db.query(Assessment).filter(Assessment.application_id == app_obj.id).order_by(Assessment.id.desc()).first()

    risks = db.query(Risk).filter(Risk.application_id == app_obj.id).all()
    total_risks = len(risks)
    high_critical = len([r for r in risks if r.severity in ["High", "Critical"] and r.status != "Resolved"])
    resolved_count = len([r for r in risks if r.status == "Resolved"])

    # Risk distribution by severity
    risk_dist = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for r in risks:
        if r.status != "Resolved":
            risk_dist[r.severity] = risk_dist.get(r.severity, 0) + 1

    # Scores
    f_score = curr_assessment.fairness_score if curr_assessment else 0.0
    t_score = curr_assessment.transparency_score if curr_assessment else 0.0
    p_score = curr_assessment.privacy_score if curr_assessment else 0.0
    s_score = curr_assessment.sustainability_score if curr_assessment else 0.0
    ov_score = curr_assessment.overall_score if curr_assessment else 0.0

    radar = [
        {"subject": "Fairness", "score": f_score, "fullMark": 100},
        {"subject": "Transparency", "score": t_score, "fullMark": 100},
        {"subject": "Data Privacy", "score": p_score, "fullMark": 100},
        {"subject": "Green AI", "score": s_score, "fullMark": 100},
    ]

    recent_assessments = [
        {
            "id": a.id,
            "name": a.name,
            "overall_score": a.overall_score,
            "date": a.completed_at.strftime("%Y-%m-%d"),
            "is_current": a.is_current
        }
        for a in db.query(Assessment).filter(Assessment.application_id == app_obj.id).order_by(Assessment.completed_at.desc()).limit(5).all()
    ]

    top_recs = db.query(Recommendation).filter(Recommendation.application_id == app_obj.id).order_by(Recommendation.id.asc()).limit(4).all()

    alerts = [
        {
            "id": r.id,
            "title": r.title,
            "severity": r.severity,
            "module": r.source_module,
            "status": r.status,
            "impact": r.business_impact
        }
        for r in [r for r in risks if r.status != "Resolved" and r.severity in ["Critical", "High"]][:5]
    ]

    latest_green = db.query(SustainabilityResult).filter(SustainabilityResult.application_id == app_obj.id).order_by(SustainabilityResult.id.desc()).first()
    co2e_sum = latest_green.estimated_co2e_kg if latest_green else 0.0

    return DashboardSummary(
        business=BusinessResponse.from_orm(business) if business else None,
        application=AIApplicationResponse.from_orm(app_obj) if app_obj else None,
        overall_governance_score=ov_score,
        fairness_score=f_score,
        transparency_score=t_score,
        privacy_score=p_score,
        sustainability_score=s_score,
        total_risks_count=total_risks,
        high_critical_risks_count=high_critical,
        resolved_risks_count=resolved_count,
        radar_data=radar,
        risk_distribution=risk_dist,
        recent_assessments=recent_assessments,
        top_recommendations=top_recs,
        recent_alerts=alerts,
        green_co2e_summary_kg=co2e_sum
    )

# ----------------- PDF REPORT DOWNLOAD -----------------
@app.get("/api/reports/{assessment_id}", tags=["Reporting"])
def download_pdf_report(
    assessment_id: int,
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    verify_business_access(current_user, a.business_id, db, include_demo=True)

    try:
        pdf_bytes = generate_assessment_pdf(db, assessment_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=RAI_Biz_Governance_Report_{assessment_id}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ----------------- DEMO SEED SCENARIO -----------------
@app.post("/api/demo/seed", tags=["Demo"])
def seed_demo_endpoint(
    db: Session = Depends(get_db)
):
    try:
        result = seed_demo_data(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- STATIC FRONTEND & SPA SERVING -----------------
dist_dir = settings.BASE_DIR.parent / "frontend" / "dist"
if (dist_dir / "index.html").exists():
    if (dist_dir / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    async def serve_root():
        return FileResponse(str(dist_dir / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = dist_dir / full_path
        if target_file.is_file():
            return FileResponse(str(target_file))
        return FileResponse(str(dist_dir / "index.html"))
else:
    @app.get("/", tags=["Root"])
    async def serve_api_welcome():
        return {
            "message": "Welcome to RAI-Biz Responsible AI Governance API",
            "docs": "/docs",
            "health": "/health",
            "status": "operational",
            "version": "1.0.0"
        }
