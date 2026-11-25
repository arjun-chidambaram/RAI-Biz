import os
import json
import random
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from ..models import (
    Business, AIApplication, Assessment, AssessmentResponse,
    Dataset, DatasetRecord, Risk, Recommendation, FairnessResult,
    ExplainabilityResult, PrivacyFinding, SustainabilityResult, IngestionLog
)
from .fairness_service import analyze_fairness, record_fairness_findings
from .xai_service import train_and_explain_model, record_explainability_findings
from .privacy_service import scan_dataframe_privacy, record_privacy_findings
from .green_ai_service import calculate_sustainability_metrics, record_sustainability_findings
from .recommendation_service import generate_and_save_recommendations
from .assessment_service import QUESTIONS_CATALOG, score_assessment
from ..config import settings

def generate_synthetic_recruitment_df(n_samples: int = 240) -> pd.DataFrame:
    """
    Generates synthetic recruitment dataset:
    candidate_id, gender, experience_years, education, test_score, qualified, selected,
    plus unredacted email, phone, and ssn for privacy screening demonstration.
    Demonstrates subtle disparate impact where female candidates have equal qualifications
    but lower historical automated selection rates.
    """
    np.random.seed(42)
    random.seed(42)

    genders = np.random.choice(["Male", "Female"], size=n_samples, p=[0.52, 0.48])
    experience = np.clip(np.random.normal(5.0, 2.8, size=n_samples), 0.5, 15.0).round(1)
    educations = np.random.choice(["Bachelors", "Masters", "PhD", "Associate"], size=n_samples, p=[0.55, 0.32, 0.08, 0.05])
    test_scores = np.clip(np.random.normal(74.0, 14.0, size=n_samples), 35.0, 99.0).round(1)

    # Qualification ground truth (pure merit: experience + test score + education)
    edu_bonus = {"PhD": 12, "Masters": 8, "Bachelors": 4, "Associate": 0}
    merit_score = (
        (test_scores * 0.55) + 
        (experience * 4.0) + 
        np.array([edu_bonus[e] for e in educations])
    )
    qualified = (merit_score >= 68.0).astype(int)

    # Simulated historical biased automated selection
    # Biased model penalized female candidates or proxy variables
    selected = []
    for g, q, m in zip(genders, qualified, merit_score):
        bias_penalty = 12.0 if g == "Female" else 0.0
        effective_score = m - bias_penalty + np.random.normal(0, 5)
        # Higher selection rate for male group
        is_sel = 1 if effective_score >= 70.0 else 0
        selected.append(is_sel)

    # PII columns to demonstrate privacy guard
    first_names_m = ["James", "David", "Robert", "Michael", "John", "William", "Daniel", "Thomas"]
    first_names_f = ["Mary", "Jennifer", "Linda", "Sarah", "Jessica", "Emily", "Ashley", "Amanda"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

    emails = []
    phones = []
    ssns = []
    names = []

    for i, g in enumerate(genders):
        f_name = random.choice(first_names_m if g == "Male" else first_names_f)
        l_name = random.choice(last_names)
        names.append(f"{f_name} {l_name}")
        emails.append(f"{f_name.lower()}.{l_name.lower()}{i}@example.com")
        phones.append(f"+1-512-{random.randint(200, 999)}-{random.randint(1000, 9999)}")
        ssns.append(f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}")

    df = pd.DataFrame({
        "candidate_id": [f"CAND-{1000 + i}" for i in range(n_samples)],
        "name": names,
        "email": emails,
        "phone": phones,
        "national_ssn": ssns,
        "gender": genders,
        "experience_years": experience,
        "education": educations,
        "test_score": test_scores,
        "qualified": qualified,
        "selected": selected
    })

    return df

def seed_demo_data(db: Session) -> Dict[str, Any]:
    """
    Seeds the SmartHire Solutions recruitment demo:
    - Business & AI Application
    - Baseline 20-question Assessment with self-reported SME gaps
    - Synthetic recruitment dataset saved to disk and database
    - Fairness analysis with 4/5ths rule disparity detected
    - Explainability SHAP analysis
    - Privacy scan detecting PII
    - Green AI sustainability analysis
    - Aggregated open risks in Central Risk Center
    - Actionable recommendations
    """
    # 1. Check if business already exists
    business = db.query(Business).filter(Business.name == "SmartHire Solutions Inc.").first()
    if not business:
        business = Business(
            name="SmartHire Solutions Inc.",
            industry="HR & Recruitment Technology",
            size="11-50",
            location="Austin, TX, USA",
            description="B2B HR SaaS provider offering automated candidate resume screening and candidate ranking engines to regional employers.",
            website="https://smarthire-demo.example.com",
            contact_email="governance@smarthire.example.com"
        )
        db.add(business)
        db.flush()

    # 2. AI Application
    application = db.query(AIApplication).filter(AIApplication.business_id == business.id, AIApplication.name == "ResumeMatcher AI").first()
    if not application:
        application = AIApplication(
            business_id=business.id,
            name="ResumeMatcher AI",
            purpose="Automated resume parsing, qualification scoring, and candidate shortlisting for client job openings.",
            business_function="Talent Acquisition & Recruitment Screening",
            data_types="Candidate Resumes, Employment History, Skills, Test Scores, Contact Information",
            automated_decision_impact="High",
            human_oversight="None",
            model_type="Ensemble Classification & Ranking",
            status="Active"
        )
        db.add(application)
        db.flush()

    # 3. Create synthetic dataset file
    df_synthetic = generate_synthetic_recruitment_df(240)
    csv_filename = "smarthire_recruitment_demo.csv"
    csv_path = settings.UPLOAD_DIR / csv_filename
    df_synthetic.to_csv(csv_path, index=False)
    
    # Also ensure bundled copy exists in settings.DATA_DIR
    try:
        data_path = settings.DATA_DIR / csv_filename
        if not data_path.exists():
            df_synthetic.to_csv(data_path, index=False)
    except Exception:
        pass

    import hashlib
    with open(csv_path, "rb") as f:
        file_bytes = f.read()
    checksum = hashlib.sha256(file_bytes).hexdigest()

    dataset = db.query(Dataset).filter(Dataset.checksum == checksum).first()
    if not dataset:
        dataset = Dataset(
            application_id=application.id,
            filename=csv_filename,
            original_filename="smarthire_recruitment_v1.csv",
            file_path=f"uploads/{csv_filename}",
            file_size_bytes=len(file_bytes),
            row_count=len(df_synthetic),
            column_count=len(df_synthetic.columns),
            checksum=checksum,
            schema_json=json.dumps({
                "columns": df_synthetic.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df_synthetic.dtypes.items()}
            }),
            schema_version="1.0",
            status="Validated"
        )
        db.add(dataset)
        db.flush()

        # Add sample records
        for idx, row in df_synthetic.head(5).iterrows():
            rec = DatasetRecord(
                dataset_id=dataset.id,
                record_type="sample",
                row_index=int(idx),
                raw_data_json=json.dumps(row.to_dict(), default=str)
            )
            db.add(rec)

    # 4. Assessment with realistic SME deficiencies
    assessment = db.query(Assessment).filter(Assessment.application_id == application.id, Assessment.name == "Initial SME Responsible AI Baseline").first()
    if not assessment:
        # Define baseline responses for 20 questions
        # Fairness: F1=Partially, F2=No, F3=No, F4=Partially, F5=No -> score = (50+0+0+50+0)/5 = 20
        # Transparency: T1=Partially, T2=No, T3=Partially, T4=No, T5=No -> score = (50+0+50+0+0)/5 = 20
        # Privacy: P1=No, P2=Yes, P3=No, P4=Yes, P5=Partially -> score = (0+100+0+100+50)/5 = 50
        # Sustainability: S1=No, S2=Partially, S3=Partially, S4=No, S5=No -> score = (0+50+50+0+0)/5 = 20
        # Overall = (20 + 20 + 50 + 20) / 4 = 27.5
        demo_answers = {
            "F1": ("Partially", "Ad-hoc gender distribution check was run on raw applicants, but no parity tests were run on model selections."),
            "F2": ("No", "Selection rates are not continuously monitored in production; no ongoing disparity drift checks exist."),
            "F3": ("No", "Rejected candidates receive generic automated rejections with no dispute or appeal mechanism."),
            "F4": ("Partially", "Some feature documentation exists in internal wikis, but proxy attributes like zip code are not mapped."),
            "F5": ("No", "No formal threshold or retraining trigger exists if selection disparity occurs."),
            "T1": ("Partially", "Global feature importances are viewed in notebooks, but individual applicants receive no explanation."),
            "T2": ("No", "Applicants are not notified that their resumes were evaluated and ranked by automated AI software."),
            "T3": ("Partially", "Application server logs exist, but feature snapshots and versioned prediction scores are not archived."),
            "T4": ("No", "Model drift and accuracy metrics are not periodically evaluated against hiring manager feedback."),
            "T5": ("No", "Top-ranked candidates are passed directly to interviews; rejected candidates receive automated rejections without human review."),
            "P1": ("No", "Applicant resumes are ingested with direct personal emails, phone numbers, and home addresses intact."),
            "P2": ("Yes", "Internal database credentials and cloud console access are protected with MFA and RBAC."),
            "P3": ("No", "Candidate data is retained indefinitely with no automated deletion schedule."),
            "P4": ("Yes", "Database storage volumes and API endpoints enforce TLS 1.3 and AES-256 at rest."),
            "P5": ("Partially", "Basic privacy policy exists on marketing website, but no AI-specific Privacy Impact Assessment was conducted."),
            "S1": ("No", "Energy consumption and inference runtime hours are not tracked on cloud GPU instances."),
            "S2": ("Partially", "Some test VMs are manually shut down on weekends, but production inference remains online 24/7."),
            "S3": ("Partially", "Simple Redis caching is used for API requests, but repetitive model passes are not systematically batched."),
            "S4": ("No", "A heavyweight 12-layer transformer was selected without benchmarking compact tree models or quantization."),
            "S5": ("No", "Cloud workload region was chosen purely by default latency rather than regional grid carbon intensity.")
        }

        dim_scores, overall, details = score_assessment([
            {"question_id": qid, "answer": ans[0], "notes": ans[1]}
            for qid, ans in demo_answers.items()
        ])

        assessment = Assessment(
            business_id=business.id,
            application_id=application.id,
            name="Initial SME Responsible AI Baseline",
            overall_score=overall,
            fairness_score=dim_scores["fairness"],
            transparency_score=dim_scores["transparency"],
            privacy_score=dim_scores["privacy"],
            sustainability_score=dim_scores["sustainability"],
            notes="Baseline governance assessment conducted for SmartHire Solutions ResumeMatcher AI. Significant gaps identified across fairness, explainability, privacy, and energy tracking.",
            is_current=True
        )
        db.add(assessment)
        db.flush()

        for qid, d in details.items():
            resp_obj = AssessmentResponse(
                assessment_id=assessment.id,
                question_id=qid,
                category=d["category"],
                question_text=d["question_text"],
                answer=d["answer"],
                score=d["score"],
                notes=d["notes"]
            )
            db.add(resp_obj)

    # 5. Run & Save Module 2: Fairness Analysis
    fairness_res = analyze_fairness(
        df=df_synthetic,
        sensitive_column="gender",
        target_column="selected",
        favorable_outcome=1,
        qualified_column="qualified"
    )
    record_fairness_findings(db, application.id, fairness_res, dataset.id, assessment.id)

    # 6. Run & Save Module 3: Explainability
    xai_res = train_and_explain_model(
        df=df_synthetic,
        target_column="selected",
        features_to_drop=["candidate_id", "name", "email", "phone", "national_ssn"],
        model_type="RandomForest"
    )
    record_explainability_findings(db, application.id, xai_res, assessment.id)

    # 7. Run & Save Module 4: Privacy Screening
    privacy_res = scan_dataframe_privacy(df_synthetic)
    record_privacy_findings(db, application.id, privacy_res, dataset.id, assessment.id)

    # 8. Run & Save Module 5: Green AI Calculation
    # 240 hours monthly runtime at 0.85 kW server load
    green_res = calculate_sustainability_metrics(
        runtime_hours=240.0,
        power_draw_kw=0.85,
        region_preset="us-east-grid"
    )
    record_sustainability_findings(db, application.id, green_res, assessment.id)

    # 9. Generate and save prioritized AI recommendations
    recs = generate_and_save_recommendations(db, application.id, assessment.id)

    db.commit()
    return {
        "business_id": business.id,
        "application_id": application.id,
        "assessment_id": assessment.id,
        "dataset_id": dataset.id,
        "overall_score": assessment.overall_score,
        "risks_count": db.query(Risk).filter(Risk.application_id == application.id).count(),
        "recommendations_count": len(recs),
        "message": "SmartHire Solutions recruitment demo successfully seeded."
    }
