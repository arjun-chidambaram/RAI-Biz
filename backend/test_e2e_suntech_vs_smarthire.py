"""
RAI-Biz End-to-End Integration & Multi-Tenant Isolation Audit
============================================================
Targets:
  - Isolated Test Database: sqlite:///./rai_biz_e2e_test.db
  - Protected Production Database: backend/rai_biz.db (Strictly protected, SHA-256 verified)

Covers the complete 16 Responsible AI Governance Modules:
  1. Email OTP Authentication & Multi-User Sessions
  2. Business & AI Application Management
  3. Overview Dashboard & Metrics Synchronization
  4. SME Responsible AI Assessment
  5. Dynamic Industry-Specific Assessment
  6. AI Fairness & Bias Detection (Automotive Data vs SmartHire Rejection)
  7. Dataset Manager & Automotive Schema Pipeline
  8. Explainable AI (XAI Dynamic Features & SHAP Explanations)
  9. Privacy Guard & Synthetic PII Heuristics
  10. Green AI Monitor & Carbon Footprint Calculation
  11. Universal Risk Intelligence Engine (Universal Scoring & Attribution)
  12. Risk Lifecycle Management & State Transitions
  13. AI Recommendations (Context-Aware Action Items)
  14. Reports & Executive PDF Generation
  15. Assessment History & Tracking
  16. Settings & Demo Workspace Isolation
"""

import os
import sys
import json
import time
import hashlib
import datetime
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.models import (
    User, EmailOTP, SessionRecord, Business, BusinessUser, AIApplication,
    Assessment, AssessmentResponse, Dataset, DatasetRecord, Risk,
    Recommendation, FairnessResult, ExplainabilityResult, PrivacyFinding,
    SustainabilityResult, IngestionLog
)
from app.services.auth_service import hash_otp
from app.services.demo_seed_service import seed_demo_data

# Paths
TEST_DB_FILE = BACKEND_DIR / "rai_biz_e2e_test.db"
PROD_DB_FILE = BACKEND_DIR / "rai_biz.db"

if TEST_DB_FILE.exists():
    try:
        os.remove(TEST_DB_FILE)
    except Exception as e:
        print(f"Notice: Could not remove old e2e test DB: {e}")

TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE.as_posix()}"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create all tables on isolated test database
Base.metadata.create_all(bind=test_engine)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def get_file_sha256(filepath: Path) -> str:
    if not filepath.exists():
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

class E2ECollector:
    def __init__(self):
        self.results = []
        self.start_time = time.time()

    def record(self, mod_num: int, mod_name: str, check_title: str, passed: bool, notes: str = ""):
        self.results.append({
            "mod_num": mod_num,
            "mod_name": mod_name,
            "check": check_title,
            "passed": passed,
            "notes": notes
        })
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} Module {mod_num:02d} ({mod_name}) -> {check_title}: {notes}")

    def summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        print("=" * 80)
        print(f"E2E AUDIT EXECUTION SUMMARY: {passed}/{total} Passed, {failed} Failed")
        print("=" * 80)
        return total, passed, failed

collector = E2ECollector()

def setup_suntech_and_smarthire(db):
    """Seed SmartHire Demo and Suntech Enterprise in the test database."""
    # 1. Seed demo data (SmartHire)
    seed_demo_data(db)

    # 2. Seed Suntech Enterprise user
    suntech_user = User(
        email="arjunchidambaram.b@gmail.com",
        full_name="Arjun Chidambaram",
        is_verified=True,
        role="business_admin"
    )
    db.add(suntech_user)
    db.commit()
    db.refresh(suntech_user)

    # 3. Seed Suntech Business
    suntech_biz = Business(
        name="Suntech Enterprise",
        industry="Automotive",
        size="Small (10-49 employees)",
        location="Chennai, India",
        description="Premium automotive detailing, ceramic coating and paint protection studio.",
        contact_email="arjunchidambaram.b@gmail.com"
    )
    db.add(suntech_biz)
    db.commit()
    db.refresh(suntech_biz)

    # 4. Link User to Business
    link = BusinessUser(
        user_id=suntech_user.id,
        business_id=suntech_biz.id,
        role="Owner"
    )
    db.add(link)

    # 5. Seed Suntech AI Application
    suntech_app = AIApplication(
        business_id=suntech_biz.id,
        name="Smart Car Detailing Assistant",
        purpose="Automated service recommendation, quote estimation, and scheduling assistant for auto detailing.",
        business_function="Customer Operations & Service Recommendation",
        data_types="Vehicle specs, service history, inspection logs, customer details",
        automated_decision_impact="Recommends detailing packages and calculates automated quotes",
        human_oversight="Technician verifies paint condition before service starts",
        model_type="RandomForest & Tabular Gradient Boosting",
        status="Testing"
    )
    db.add(suntech_app)
    db.commit()
    db.refresh(suntech_app)

    # 6. Seed Suntech Automotive Dataset (ID 2 in test DB, associated with suntech_app.id)
    # Read the generated CSV
    csv_path = BACKEND_DIR / "uploads" / "suntech_car_detailing_dataset.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing {csv_path}")

    with open(csv_path, "rb") as f:
        csv_bytes = f.read()

    checksum = hashlib.sha256(csv_bytes).hexdigest()
    suntech_dataset = Dataset(
        application_id=suntech_app.id,
        filename="suntech_car_detailing_dataset.csv",
        original_filename="suntech_car_detailing_dataset.csv",
        file_path=str(csv_path),
        file_size_bytes=len(csv_bytes),
        row_count=250,
        column_count=12,
        schema_json=json.dumps([
            "booking_id", "customer_gender", "customer_age_group", "vehicle_type",
            "vehicle_age_years", "paint_condition_score", "service_package",
            "quote_amount_inr", "lead_time_days", "service_approved", "phone", "email"
        ]),
        checksum=checksum,
        status="Ingested"
    )
    db.add(suntech_dataset)
    db.commit()
    db.refresh(suntech_dataset)

    s_user_id = suntech_user.id
    s_biz_id = suntech_biz.id
    s_app_id = suntech_app.id
    s_dataset_id = suntech_dataset.id

    return s_user_id, s_biz_id, s_app_id, s_dataset_id


def run_e2e_audit():
    print("=" * 80)
    print("RAI-BIZ COMPREHENSIVE END-TO-END INTEGRATION AUDIT")
    print("=" * 80)
    
    prod_sha_before = get_file_sha256(PROD_DB_FILE)
    print(f"Production DB Target: {PROD_DB_FILE}")
    print(f"Production DB SHA-256 (Pre-Audit): {prod_sha_before}")
    print("-" * 80)

    db = TestSessionLocal()
    s_user_id, s_biz_id, s_app_id, s_dataset_id = setup_suntech_and_smarthire(db)
    db.close()

    # ----------------------------------------------------
    # MODULE 1: AUTHENTICATION & MULTI-USER SESSIONS
    # ----------------------------------------------------
    print("\n--- 1. Testing Email OTP Authentication & Sessions ---")
    with patch("app.services.email_service.resend.Emails.send", return_value={"id": "mock_id"}):
        res = client.post("/api/auth/send-otp", json={"email": "arjunchidambaram.b@gmail.com"})
        collector.record(1, "Authentication", "Send OTP for Suntech User",
                         res.status_code == 200, f"Status: {res.status_code}")

    # Set valid OTP in DB
    db = TestSessionLocal()
    otp_row = db.query(EmailOTP).filter(EmailOTP.email == "arjunchidambaram.b@gmail.com", EmailOTP.is_used == False).order_by(EmailOTP.id.desc()).first()
    test_otp = "123456"
    otp_row.otp_hash = hash_otp("arjunchidambaram.b@gmail.com", test_otp)
    db.commit()
    db.close()

    res = client.post("/api/auth/verify-otp", json={"email": "arjunchidambaram.b@gmail.com", "otp": test_otp})
    collector.record(1, "Authentication", "Verify OTP & Session Creation",
                     res.status_code == 200 and "user" in res.json(), f"User: {res.json().get('user', {}).get('email')}")

    # Check status endpoint (/api/auth/me)
    res = client.get("/api/auth/me")
    auth_data = res.json()
    collector.record(1, "Authentication", "Active Auth Status Returns Suntech Context",
                     auth_data.get("authenticated") is True and auth_data.get("business", {}).get("name") == "Suntech Enterprise",
                     f"Business: {auth_data.get('business', {}).get('name')}, App: {auth_data.get('application', {}).get('name')}")

    # ----------------------------------------------------
    # MODULE 2: BUSINESS & APPLICATION MANAGEMENT
    # ----------------------------------------------------
    print("\n--- 2. Testing Business & Application Management ---")
    res = client.get("/api/businesses")
    businesses = res.json()
    has_suntech = any(b["name"] == "Suntech Enterprise" for b in businesses)
    collector.record(2, "Business Management", "User Business Retrieval",
                     res.status_code == 200 and has_suntech, f"Found {len(businesses)} businesses for Suntech user")

    res = client.get(f"/api/applications?business_id={s_biz_id}")
    apps = res.json()
    collector.record(2, "Application Management", "Suntech Applications Listed",
                     len(apps) >= 1 and apps[0]["name"] == "Smart Car Detailing Assistant",
                     f"App: {apps[0]['name']}, Industry Context: Automotive")

    # ----------------------------------------------------
    # MODULE 3: OVERVIEW DASHBOARD
    # ----------------------------------------------------
    print("\n--- 3. Testing Overview Dashboard ---")
    res = client.get("/api/dashboard")
    dash = res.json()
    collector.record(3, "Dashboard", "Dashboard Overview Metrics Loaded",
                     res.status_code == 200 and "overall_governance_score" in dash and "total_risks_count" in dash,
                     f"Dashboard Score: {dash.get('overall_governance_score')}, Risks: {dash.get('total_risks_count')}")

    # ----------------------------------------------------
    # MODULE 4 & 5: DYNAMIC ASSESSMENT (AUTOMOTIVE SPECIFIC)
    # ----------------------------------------------------
    print("\n--- 4 & 5. Testing Dynamic SME Assessment for Automotive ---")
    res = client.post("/api/assessments/generate-questions", json={"application_id": s_app_id, "force_llm": False})
    q_data = res.json()
    collector.record(5, "Dynamic Assessment", "Automotive Dynamic Question Generation",
                     res.status_code == 200 and len(q_data.get("questions", [])) >= 10,
                     f"Generated {len(q_data.get('questions', []))} questions, Industry: {q_data.get('industry')}")

    # Submit an assessment for Suntech
    assessment_payload = {
        "business_id": s_biz_id,
        "application_id": s_app_id,
        "industry": "Automotive",
        "question_version": "2.0-dynamic",
        "name": "Suntech Automotive AI Governance Assessment",
        "responses": [
            {
                "question_id": "P1",
                "category": "Privacy",
                "question_text": "Are customer contact numbers and emails masked in automotive job logs?",
                "guidance": "Prevent exposure of customer personal data.",
                "evidence_required": "PII redaction policy",
                "risk_severity": "High",
                "recommendation_text": "Implement automated masking on phone and email columns.",
                "answer": "No",
                "notes": "Currently stored in plain text in detailing job logs."
            },
            {
                "question_id": "F1",
                "category": "Fairness",
                "question_text": "Do automated detailing quotes vary systematically based on customer gender or age?",
                "guidance": "Pricing algorithms must not bias quotes by demographic attributes.",
                "evidence_required": "Disparate impact analysis",
                "risk_severity": "High",
                "recommendation_text": "Audit service quote amounts by gender and age group.",
                "answer": "Yes",
                "notes": "Statistical disparity checks conducted."
            },
            {
                "question_id": "T1",
                "category": "Transparency",
                "question_text": "Can customers see why specific ceramic coating packages are recommended?",
                "guidance": "Explain vehicle age and paint condition factors.",
                "evidence_required": "Recommendation explanation printout",
                "risk_severity": "Medium",
                "recommendation_text": "Provide customer with key factor checklist.",
                "answer": "Yes",
                "notes": "Technicians explain paint condition scores."
            },
            {
                "question_id": "S1",
                "category": "Sustainability",
                "question_text": "Are server resources rightsized for detailing recommendation batches?",
                "guidance": "Run lightweight models on CPU instead of heavy GPU clusters.",
                "evidence_required": "Compute efficiency review",
                "risk_severity": "Low",
                "recommendation_text": "Maintain CPU inference.",
                "answer": "Yes",
                "notes": "Low energy compute footprint."
            }
        ]
    }

    res = client.post("/api/assessments", json=assessment_payload)
    suntech_assessment = res.json()
    collector.record(4, "SME Assessment", "Submit Assessment & Calculate Dimension Scores",
                     res.status_code == 200 and suntech_assessment.get("overall_score") is not None,
                     f"Overall Score: {suntech_assessment.get('overall_score')}, Privacy: {suntech_assessment.get('privacy_score')}, Fairness: {suntech_assessment.get('fairness_score')}")

    # ----------------------------------------------------
    # MODULE 6: FAIRNESS & BIAS DETECTION (WITH CROSS-APP PROTECTION)
    # ----------------------------------------------------
    print("\n--- 6. Testing Fairness & Bias Detection & Cross-App Protection ---")
    
    # Positive Test: Run on Suntech dataset with automotive columns
    fairness_req = {
        "application_id": s_app_id,
        "dataset_id": s_dataset_id,
        "sensitive_attribute": "customer_gender",
        "target_attribute": "service_approved",
        "favorable_outcome": 1
    }
    res = client.post("/api/fairness/analyze", json=fairness_req)
    fairness_res = res.json()
    collector.record(6, "Fairness", "Automotive Fairness Analysis on customer_gender",
                     res.status_code == 200 and "demographic_parity_diff" in fairness_res,
                     f"DP Diff: {fairness_res.get('demographic_parity_diff')}, Passed 4/5ths: {fairness_res.get('four_fifths_rule_passed')}")

    # Cross-Application Leak Prevention Test: Attempt to evaluate Suntech App using SmartHire Dataset (ID 1)
    smarthire_dataset_id = 1
    leak_req = {
        "application_id": s_app_id,
        "dataset_id": smarthire_dataset_id,
        "sensitive_attribute": "gender",
        "target_attribute": "selected",
        "favorable_outcome": 1
    }
    res = client.post("/api/fairness/analyze", json=leak_req)
    collector.record(6, "Fairness", "CROSS-APP PROTECTION: Reject Foreign Dataset ID 1 on Suntech",
                     res.status_code == 400 and ("not associated" in res.json().get("detail", "") or "does not belong" in res.json().get("detail", "")),
                     f"HTTP {res.status_code}: {res.json().get('detail')}")

    # ----------------------------------------------------
    # MODULE 7: DATASET MANAGER
    # ----------------------------------------------------
    print("\n--- 7. Testing Dataset Manager ---")
    res = client.get(f"/api/datasets?application_id={s_app_id}")
    ds_list = res.json()
    collector.record(7, "Dataset Manager", "Application Scoped Dataset Query",
                     res.status_code == 200 and len(ds_list) >= 1 and ds_list[0]["id"] == s_dataset_id,
                     f"Found {len(ds_list)} datasets for Suntech App {s_app_id}")

    res = client.get(f"/api/datasets/{s_dataset_id}/preview")
    preview = res.json()
    collector.record(7, "Dataset Manager", "Dataset Preview & Column Schemas",
                     res.status_code == 200 and "paint_condition_score" in preview.get("columns", []),
                     f"Rows: {preview.get('row_count')}, Columns: {len(preview.get('columns', []))}")

    # ----------------------------------------------------
    # MODULE 8: EXPLAINABLE AI (XAI) (WITH CROSS-APP PROTECTION)
    # ----------------------------------------------------
    print("\n--- 8. Testing Explainable AI & Cross-App Protection ---")
    
    # Positive Test: Run on Suntech dataset with dynamic target attribute
    xai_req = {
        "application_id": s_app_id,
        "dataset_id": s_dataset_id,
        "target_attribute": "service_approved",
        "model_type": "RandomForest"
    }
    res = client.post("/api/explainability/analyze", json=xai_req)
    xai_res = res.json()
    collector.record(8, "Explainable AI", "Train & Explain Model on Automotive Features",
                     res.status_code == 200 and len(xai_res.get("global_importance", [])) > 0,
                     f"Model: {xai_res.get('model_name')}, Features: {len(xai_res.get('global_importance', []))}, Accuracy: {xai_res.get('model_accuracy')}")

    # Cross-Application Leak Prevention Test: Attempt to evaluate Suntech App using SmartHire Dataset (ID 1)
    res = client.post("/api/explainability/analyze", json={"application_id": s_app_id, "dataset_id": smarthire_dataset_id})
    collector.record(8, "Explainable AI", "CROSS-APP PROTECTION: Reject Foreign Dataset ID 1 on Suntech",
                     res.status_code == 400 and ("not associated" in res.json().get("detail", "") or "does not belong" in res.json().get("detail", "")),
                     f"HTTP {res.status_code}: {res.json().get('detail')}")

    # ----------------------------------------------------
    # MODULE 9: PRIVACY GUARD (WITH CROSS-APP PROTECTION)
    # ----------------------------------------------------
    print("\n--- 9. Testing Privacy Guard & Cross-App Protection ---")
    
    # Positive Test: Scan Suntech dataset for synthetic PII
    privacy_req = {
        "application_id": s_app_id,
        "dataset_id": s_dataset_id
    }
    res = client.post("/api/privacy/scan", json=privacy_req)
    priv_res = res.json()
    has_pii = priv_res.get("pii_detected_count", 0) > 0
    collector.record(9, "Privacy Guard", "PII Heuristic Screening on Automotive Dataset",
                     res.status_code == 200 and has_pii,
                     f"Detected {priv_res.get('pii_detected_count')} PII patterns, Findings: {len(priv_res.get('findings', []))}")

    # Cross-Application Leak Prevention Test: Attempt to evaluate Suntech App using SmartHire Dataset (ID 1)
    res = client.post("/api/privacy/scan", json={"application_id": s_app_id, "dataset_id": smarthire_dataset_id})
    collector.record(9, "Privacy Guard", "CROSS-APP PROTECTION: Reject Foreign Dataset ID 1 on Suntech",
                     res.status_code == 400 and ("not associated" in res.json().get("detail", "") or "does not belong" in res.json().get("detail", "")),
                     f"HTTP {res.status_code}: {res.json().get('detail')}")

    # ----------------------------------------------------
    # MODULE 10: GREEN AI MONITOR
    # ----------------------------------------------------
    print("\n--- 10. Testing Green AI Monitor ---")
    green_req = {
        "application_id": s_app_id,
        "compute_duration_hours": 120.0,
        "power_draw_kw": 0.45,
        "region_preset": "us-east-grid"
    }
    res = client.post("/api/sustainability/calculate", json=green_req)
    green_res = res.json()
    collector.record(10, "Green AI Monitor", "Carbon Footprint & Energy Calculation",
                     res.status_code == 200 and "energy_kwh" in green_res and "estimated_co2e_kg" in green_res,
                     f"Energy: {green_res.get('energy_kwh')} kWh, Carbon: {green_res.get('estimated_co2e_kg')} kgCO2e")

    # ----------------------------------------------------
    # MODULE 11: UNIVERSAL RISK INTELLIGENCE ENGINE
    # ----------------------------------------------------
    print("\n--- 11. Testing Universal Risk Intelligence Engine ---")
    res = client.get(f"/api/risks?application_id={s_app_id}")
    risks_generated = res.json()
    collector.record(11, "Risk Engine", "Generate Universal Risks for Automotive App",
                     res.status_code == 200 and len(risks_generated) > 0,
                     f"Generated {len(risks_generated)} risks across governance dimensions")

    # Verify severity and evidence attribution accuracy
    all_have_evidence = all(r.get("evidence") for r in risks_generated)
    valid_severities = all(r.get("severity") in ["Critical", "High", "Medium", "Low"] for r in risks_generated)
    collector.record(11, "Risk Engine", "Severity Calculation & Evidence Attribution Integrity",
                     all_have_evidence and valid_severities,
                     f"All risks have explicit evidence basis and standardized severities")

    # ----------------------------------------------------
    # MODULE 12: RISK LIFECYCLE MANAGEMENT
    # ----------------------------------------------------
    print("\n--- 12. Testing Risk Lifecycle Management ---")
    first_risk_id = risks_generated[0]["id"]
    transition_req = {
        "status": "In progress",
        "completion_notes": "Configured regex PII masking rules in data ingestion pipeline."
    }
    res = client.patch(f"/api/risks/{first_risk_id}", json=transition_req)
    updated_risk = res.json()
    collector.record(12, "Risk Lifecycle", "Transition Risk State to In progress",
                     res.status_code == 200 and updated_risk.get("status") == "In progress",
                     f"Risk {first_risk_id} new status: {updated_risk.get('status')}")

    # Further transition to Resolved
    res = client.patch(f"/api/risks/{first_risk_id}", json={"status": "Resolved", "completion_notes": "Masking deployed and verified."})
    collector.record(12, "Risk Lifecycle", "Transition Risk State to Resolved",
                     res.status_code == 200 and res.json().get("status") == "Resolved",
                     f"Risk {first_risk_id} finalized as Resolved")

    # ----------------------------------------------------
    # MODULE 13: AI RECOMMENDATIONS
    # ----------------------------------------------------
    print("\n--- 13. Testing AI Recommendations Engine ---")
    res = client.get(f"/api/recommendations?application_id={s_app_id}")
    recs = res.json()
    collector.record(13, "AI Recommendations", "Context-Aware Action Items Retrieved",
                     res.status_code == 200 and len(recs) > 0,
                     f"Retrieved {len(recs)} tailored recommendations for Suntech Detailing")

    # ----------------------------------------------------
    # MODULE 14: REPORTS & PDF GENERATION
    # ----------------------------------------------------
    print("\n--- 14. Testing Reports & PDF Generation ---")
    res = client.get(f"/api/reports/{suntech_assessment['id']}")
    is_pdf = res.headers.get("content-type") == "application/pdf"
    has_bytes = len(res.content) > 1000
    collector.record(14, "Reports & PDF", "Generate Executive PDF Governance Report",
                     res.status_code == 200 and is_pdf and has_bytes,
                     f"PDF Size: {len(res.content)} bytes, Content-Type: {res.headers.get('content-type')}")

    # ----------------------------------------------------
    # MODULE 15: ASSESSMENT HISTORY
    # ----------------------------------------------------
    print("\n--- 15. Testing Assessment History ---")
    res = client.get(f"/api/assessments?application_id={s_app_id}")
    history = res.json()
    collector.record(15, "Assessment History", "Historical Assessment Query for Suntech",
                     res.status_code == 200 and len(history) >= 1,
                     f"Found {len(history)} historical assessments for App {s_app_id}")

    # ----------------------------------------------------
    # MODULE 16: SETTINGS & DEMO WORKSPACE ISOLATION
    # ----------------------------------------------------
    print("\n--- 16. Testing Settings & Demo Workspace Isolation ---")
    # 16.1 Re-seed Demo Scenario (SmartHire)
    res = client.post("/api/demo/seed")
    collector.record(16, "Demo Workspace", "Trigger SmartHire Demo Scenario Seeder",
                     res.status_code == 200 and "SmartHire" in str(res.json()),
                     f"Message: {res.json().get('message')}")

    # 16.2 Verify Suntech context is preserved and not overwritten by demo seed
    res = client.get("/api/businesses/profile")
    profile = res.json()
    collector.record(16, "Multi-Tenant Isolation", "Demo Seeder Preserves Suntech Business Profile",
                     profile.get("business", {}).get("name") == "Suntech Enterprise" and profile.get("application", {}).get("name") == "Smart Car Detailing Assistant",
                     f"Current Business: {profile.get('business', {}).get('name')}, App: {profile.get('application', {}).get('name')}")

    # 16.3 Cross-Tenant Isolation: Create a foreign user session and verify 403 on Suntech assessment
    db = TestSessionLocal()
    foreign_user = User(email="other.business@example.com", full_name="Foreign SME", is_verified=True)
    db.add(foreign_user)
    db.commit()
    db.refresh(foreign_user)
    
    foreign_token = "sess_foreign_user_token_99999"
    db.add(SessionRecord(
        user_id=foreign_user.id,
        session_hash=hashlib.sha256(foreign_token.encode()).hexdigest(),
        created_at=datetime.datetime.utcnow(),
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=7)
    ))
    db.commit()
    db.close()

    foreign_client = TestClient(app)
    foreign_client.cookies.set(settings.SESSION_COOKIE_NAME, foreign_token)

    res_cross = foreign_client.get(f"/api/assessments/{suntech_assessment['id']}")
    collector.record(16, "Multi-Tenant Isolation", "Cross-Tenant Private Assessment Protection (403)",
                     res_cross.status_code == 403,
                     f"Foreign User access HTTP Status: {res_cross.status_code}")

    # ----------------------------------------------------
    # PRODUCTION DATABASE PRESERVATION VERIFICATION
    # ----------------------------------------------------
    print("\n--- Production Database Integrity Check ---")
    prod_sha_after = get_file_sha256(PROD_DB_FILE)
    print(f"Production DB SHA-256 (Post-Audit): {prod_sha_after}")
    db_unmodified = (prod_sha_before == prod_sha_after) and (prod_sha_before != "FILE_NOT_FOUND")
    collector.record(16, "Database Integrity", "Production Database backend/rai_biz.db Unmodified",
                     db_unmodified,
                     f"Pre: {prod_sha_before[:16]}... | Post: {prod_sha_after[:16]}... (Identical: {db_unmodified})")

    # Final summary
    total, passed, failed = collector.summary()
    return total, passed, failed

if __name__ == "__main__":
    t, p, f = run_e2e_audit()
    sys.exit(0 if f == 0 else 1)
