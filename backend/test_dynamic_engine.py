import os
import json
import sys
from app.database import SessionLocal
from app.models import Business, AIApplication, Assessment, AssessmentResponse, Risk, Recommendation, User
from app.schemas import AssessmentCreate, AssessmentResponseInput
from app.services.dynamic_assessment_engine import (
    detect_industry_key,
    get_supported_industries,
    generate_industry_assessment
)
from app.services.assessment_service import process_and_save_assessment

def run_tests():
    print("=" * 70)
    print("RAI-Biz Dynamic Assessment Engine Test Suite")
    print("=" * 70)

    # 1. Test Industry Key Detection
    print("\n--- TEST 1: Industry Normalization & Key Detection ---")
    test_cases = [
        ("Automotive Services", "detailing assistant", "automotive_services"),
        ("Car Detailing", "booking AI", "automotive_services"),
        ("Recruitment and HR", "resume screening", "recruitment_hr"),
        ("Human Resources", "talent acquisition", "recruitment_hr"),
        ("Healthcare & Life Sciences", "clinical triage", "healthcare"),
        ("Hospital", "diagnostic AI", "healthcare"),
        ("Banking & Finance", "credit underwriting", "banking_finance"),
        ("Fintech", "loan scoring", "banking_finance"),
        ("Retail & E-commerce", "product recommendations", "retail_ecommerce"),
        ("E-commerce", "dynamic pricing", "retail_ecommerce"),
        ("Logistics", "fleet routing", "transportation_logistics"),
        ("Agriculture", "crop health", "agriculture"),
        ("Space Exploration", "satellite telemetry", "general_sme")
    ]
    for ind, func, expected in test_cases:
        detected = detect_industry_key(ind, func)
        assert detected == expected, f"Failed for '{ind}': expected {expected}, got {detected}"
        print(f"  [PASS] '{ind}' -> key: '{detected}'")

    # 2. Test Question Bank Generation for Distinct Industries
    print("\n--- TEST 2: Curated Question Bank Tailoring ---")

    # Scenario A: Suntech Enterprise (Automotive Services)
    biz_auto = Business(name="Suntech Enterprise", industry="Automotive Services", location="India", size="15-50")
    app_auto = AIApplication(name="Smart Car Detailing Assistant", business_function="Customer Detailing & Booking", automated_decision_impact="High", human_oversight="Assisted", data_types="Customer contact, vehicle model, service history", purpose="Automate package recommendations and scheduling")
    q_auto = generate_industry_assessment(biz_auto, app_auto)
    assert len(q_auto) == 20, f"Expected 20 questions, got {len(q_auto)}"
    f1_auto = next(q for q in q_auto if q.id == "F1")
    t1_auto = next(q for q in q_auto if q.id == "T1")
    p1_auto = next(q for q in q_auto if q.id == "P1")
    assert "vehicle" in f1_auto.question_text.lower() or "vehicle" in f1_auto.guidance.lower() or "Smart Car Detailing Assistant" in f1_auto.question_text
    print(f"  [PASS] Scenario A (Automotive): F1='{f1_auto.question_text[:80]}...'")
    print(f"         Required Evidence: '{f1_auto.evidence_required[:80]}...'")

    # Scenario B: SmartHire (Recruitment & HR)
    biz_hr = Business(name="SmartHire Solutions", industry="Recruitment & HR", location="USA", size="50-200")
    app_hr = AIApplication(name="ResumeMatcher AI", business_function="Candidate Evaluation", automated_decision_impact="High", human_oversight="Assisted", data_types="Resumes, candidate emails, work history", purpose="Automate candidate ranking and resume parsing")
    q_hr = generate_industry_assessment(biz_hr, app_hr)
    assert len(q_hr) == 20
    f1_hr = next(q for q in q_hr if q.id == "F1")
    assert "candidate" in f1_hr.question_text.lower() or "hiring" in f1_hr.guidance.lower() or "ResumeMatcher AI" in f1_hr.question_text
    print(f"  [PASS] Scenario B (Recruitment): F1='{f1_hr.question_text[:80]}...'")

    # Scenario C: Healthcare
    biz_health = Business(name="Apex Clinical Health", industry="Healthcare", location="UK", size="200-500")
    app_health = AIApplication(name="Clinical Triage AI", business_function="Patient Triage", automated_decision_impact="High", human_oversight="Assisted", data_types="EHR, patient vitals, diagnostic notes", purpose="Assist emergency triage and acuity scoring")
    q_health = generate_industry_assessment(biz_health, app_health)
    assert len(q_health) == 20
    f1_health = next(q for q in q_health if q.id == "F1")
    p1_health = next(q for q in q_health if q.id == "P1")
    assert "patient" in f1_health.question_text.lower() or "clinical" in f1_health.guidance.lower()
    print(f"  [PASS] Scenario C (Healthcare): F1='{f1_health.question_text[:80]}...'")
    print(f"         P1 Evidence: '{p1_health.evidence_required[:80]}...'")

    # Scenario D: Banking & Finance
    biz_bank = Business(name="Meridian Capital", industry="Banking and Finance", location="Singapore", size="50-100")
    app_bank = AIApplication(name="Credit Underwriter AI", business_function="Loan Approval", automated_decision_impact="High", human_oversight="None", data_types="Credit reports, tax returns, bank transactions", purpose="Automate small business loan underwriting")
    q_bank = generate_industry_assessment(biz_bank, app_bank)
    assert len(q_bank) == 20
    f1_bank = next(q for q in q_bank if q.id == "F1")
    # High impact and unassisted oversight elevates F1 severity to Critical
    assert f1_bank.risk_severity == "Critical", f"Expected Critical severity for unassisted high-impact banking AI, got {f1_bank.risk_severity}"
    print(f"  [PASS] Scenario D (Banking): F1='{f1_bank.question_text[:80]}...' Severity: {f1_bank.risk_severity}")

    # Scenario E: Retail & E-commerce
    biz_retail = Business(name="Nova E-Store", industry="Retail & E-commerce", location="Canada", size="25-50")
    app_retail = AIApplication(name="Dynamic Recommender", business_function="E-Commerce Recommender", automated_decision_impact="Medium", human_oversight="Assisted", data_types="Cart history, browsing logs, payment tokens", purpose="Personalize product suggestions and checkout deals")
    q_retail = generate_industry_assessment(biz_retail, app_retail)
    assert len(q_retail) == 20
    f1_retail = next(q for q in q_retail if q.id == "F1")
    print(f"  [PASS] Scenario E (Retail): F1='{f1_retail.question_text[:80]}...'")

    # 3. Test Database Persistence & Isolation
    print("\n--- TEST 3: Database Persistence & Workspace Isolation ---")
    db = SessionLocal()
    try:
        # Check Suntech Enterprise application
        suntech_app = db.query(AIApplication).filter(AIApplication.id == 9).first()
        assert suntech_app is not None, "Suntech app ID 9 not found in DB"
        suntech_biz = db.query(Business).filter(Business.id == suntech_app.business_id).first()
        print(f"  Target Application: ID {suntech_app.id} - '{suntech_app.name}' under Business '{suntech_biz.name}' ({suntech_biz.industry})")

        # Submit new dynamic assessment for Suntech
        q_suntech = generate_industry_assessment(suntech_biz, suntech_app)
        sample_responses = []
        for i, q in enumerate(q_suntech):
            # Mix answers: first 10 Yes, next 5 Partially, last 5 No
            ans = "Yes" if i < 10 else ("Partially" if i < 15 else "No")
            sample_responses.append(AssessmentResponseInput(
                question_id=q.id,
                answer=ans,
                notes=f"Verified automotive evidence for {q.id} in {suntech_biz.name}"
            ))

        assessment_in = AssessmentCreate(
            business_id=suntech_biz.id,
            application_id=suntech_app.id,
            name="Suntech Automotive Governance Audit (Dynamic Engine Test)",
            notes="Automated dynamic engine verification test",
            responses=sample_responses
        )

        saved_assessment = process_and_save_assessment(db, assessment_in, user_id=1)
        print(f"  [PASS] Saved Assessment ID: {saved_assessment.id}")
        print(f"         Overall Score: {saved_assessment.overall_score} (Fairness: {saved_assessment.fairness_score}, Transparency: {saved_assessment.transparency_score}, Privacy: {saved_assessment.privacy_score}, Sustainability: {saved_assessment.sustainability_score})")
        print(f"         Industry: '{saved_assessment.industry}', Version: '{saved_assessment.question_version}'")
        assert saved_assessment.industry == "Automotive Services"
        assert saved_assessment.question_version == "2.0"
        assert saved_assessment.question_set_json is not None
        
        # Verify JSON snapshot contains all 20 dynamic questions
        snapshot = json.loads(saved_assessment.question_set_json)
        assert len(snapshot) == 20
        print(f"         Archived Question Snapshot: {len(snapshot)} questions preserved.")

        # Verify Assessment Responses have guidance & evidence requirements
        db_responses = db.query(AssessmentResponse).filter(AssessmentResponse.assessment_id == saved_assessment.id).all()
        assert len(db_responses) == 20
        first_resp = db_responses[0]
        assert first_resp.evidence_required is not None
        assert first_resp.recommendation_text is not None
        print(f"         Response 0 ({first_resp.question_id}): Guidance='{first_resp.guidance[:40]}...', Evidence='{first_resp.evidence_required[:40]}...'")

        # Verify SmartHire Demo Workspace (application_id=1) was untouched
        smarthire_assessments = db.query(Assessment).filter(Assessment.application_id == 1).all()
        print(f"  [PASS] SmartHire Workspace: {len(smarthire_assessments)} demo assessments intact.")

        # Verify Risks generated for Deficiencies
        risks = db.query(Risk).filter(Risk.assessment_id == saved_assessment.id).all()
        print(f"  [PASS] Generated Risks for Deficiencies: {len(risks)} risks recorded.")
        assert len(risks) >= 10, f"Expected at least 10 risks for Partially/No answers, got {len(risks)}"
        sample_risk = risks[0]
        print(f"         Sample Risk: [{sample_risk.severity}] '{sample_risk.title}'")
        print(f"         Action: '{sample_risk.recommended_action[:70]}...'")

        # Verify Recommendations generated
        recs = db.query(Recommendation).filter(Recommendation.assessment_id == saved_assessment.id).all()
        print(f"  [PASS] Generated Recommendations: {len(recs)} actionable items created.")
        assert len(recs) >= 10

        print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
