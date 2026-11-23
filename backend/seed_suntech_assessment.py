import sys
sys.path.insert(0, ".")
from app.database import SessionLocal
from app.models import Business, AIApplication, Assessment, AssessmentResponse, Risk, Recommendation
from app.services.assessment_service import score_assessment, QUESTIONS_CATALOG
from app.services.recommendation_service import generate_and_save_recommendations

def seed_suntech():
    db = SessionLocal()
    app_obj = db.query(AIApplication).filter(AIApplication.id == 9).first()
    assert app_obj is not None, "App 9 not found"
    biz = db.query(Business).filter(Business.id == app_obj.business_id).first()
    assert biz is not None, "Biz 9 not found"

    # Clear any previous test assessments for App 9 only (keeping Demo App 1 untouched)
    prev_assessments = db.query(Assessment).filter(Assessment.application_id == 9).all()
    for a in prev_assessments:
        db.query(AssessmentResponse).filter(AssessmentResponse.assessment_id == a.id).delete()
        db.query(Risk).filter(Risk.assessment_id == a.id).delete()
        db.delete(a)
    db.commit()

    answers_map = {
        "F1": ("Partially", "Ad-hoc checks were run comparing recommended packages across vehicle age/tier brackets, but statistical parity tests across customer demographic segments are not conducted."),
        "F2": ("No", "Service quote discount rates and package acceptance are not tracked continuously across customer demographics or vehicle categories."),
        "F3": ("Partially", "Customers can contact detailing shop staff via phone/email to question a package recommendation or price quote, but no formal algorithmic dispute channel exists."),
        "F4": ("Partially", "Customer postal code and vehicle luxury tier are recorded in the system, but proxy risk documentation for pricing disparity has not been completed."),
        "F5": ("No", "No formal corrective action protocol or retraining trigger is documented if package recommendation rates show demographic or geographic disparity."),
        "T1": ("Partially", "Assistant shows package summaries based on vehicle finish/mileage, but lacks local SHAP feature attribution explanations for why premium ceramic treatments are proposed."),
        "T2": ("Partially", "The website booking widget has a small AI badge, but automated quote emails and SMS appointment confirmations do not explicitly disclose that recommendations are AI-generated."),
        "T3": ("Partially", "Booking transactions and timestamps are recorded in the database, but input snapshots of customer vehicle inquiries and model confidence scores are not immutably logged."),
        "T4": ("No", "Model recommendation accuracy and seasonal car care trend drifts are not periodically evaluated against technician inspection logs."),
        "T5": ("Partially", "Service advisors review high-value quotes (e.g., multi-stage paint correction over $500), but standard wash and interior packages are booked without human review."),
        "P1": ("No", "Customer phone numbers, license plate numbers, and vehicle registration details are ingested into the assistant prompt without automated PII masking."),
        "P2": ("Partially", "Manager access to CRM records requires individual credentials, but service bay technicians share a common tablet login without MFA."),
        "P3": ("No", "Customer vehicle inquiry transcripts, license plate photos, and booking logs are stored indefinitely with no automated deletion schedule."),
        "P4": ("Yes", "Customer booking data transmissions use TLS 1.3 encryption, and offsite database backups are encrypted at rest with AES-256."),
        "P5": ("No", "No formal Privacy Impact Assessment (PIA) or third-party vetting has been conducted for external LLM APIs integrated into the customer assistant."),
        "S1": ("No", "Compute duration and energy consumption for running the customer recommendation assistant are not tracked or monitored."),
        "S2": ("Partially", "Customer-facing inference instances auto-scale during daytime hours, but staging/dev containers run 24/7 without idle shutdown."),
        "S3": ("Partially", "Standard package suggestions for popular vehicle models hit a basic cache, but free-text customer queries trigger fresh deep neural inference calls."),
        "S4": ("No", "The assistant uses a general 7B parameter foundation model for routine appointment matching and package filtering rather than lightweight models."),
        "S5": ("No", "Cloud infrastructure is deployed in a standard commercial data center region without evaluating grid carbon intensity or renewable energy availability.")
    }

    raw_responses = [{"question_id": q_id, "answer": val[0], "notes": val[1]} for q_id, val in answers_map.items()]
    dim_scores, overall, details = score_assessment(raw_responses)

    print("Calculated Dimension Scores:", dim_scores)
    print("Calculated Overall Score:", overall)
    assert dim_scores["fairness"] == 30.0
    assert dim_scores["transparency"] == 40.0
    assert dim_scores["privacy"] == 30.0
    assert dim_scores["sustainability"] == 20.0
    assert overall == 30.0

    assessment = Assessment(
        business_id=biz.id,
        application_id=app_obj.id,
        name="Suntech Enterprise Baseline Governance Audit",
        overall_score=overall,
        fairness_score=dim_scores["fairness"],
        transparency_score=dim_scores["transparency"],
        privacy_score=dim_scores["privacy"],
        sustainability_score=dim_scores["sustainability"],
        notes="Baseline Responsible AI Governance assessment for Suntech Enterprise Smart Car Detailing Assistant.",
        is_current=True
    )
    db.add(assessment)
    db.flush()

    for q_id, d in details.items():
        resp_obj = AssessmentResponse(
            assessment_id=assessment.id,
            question_id=q_id,
            category=d["category"],
            question_text=d["question_text"],
            answer=d["answer"],
            score=d["score"],
            notes=d["notes"]
        )
        db.add(resp_obj)

        if d["answer"] in ["No", "Partially"]:
            severity = "High" if d["answer"] == "No" else "Medium"
            if q_id in ["F1", "T5", "P1", "P4"] and d["answer"] == "No":
                severity = "Critical"

            q_def = next((q for q in QUESTIONS_CATALOG if q.id == q_id), None)
            why_it_matters = q_def.why_it_matters if q_def else "Creates governance exposure."

            risk = Risk(
                application_id=app_obj.id,
                assessment_id=assessment.id,
                title=f"Deficiency in {d['category'].title()}: {q_id}",
                description=f"Assessment finding for '{d['question_text']}': Self-reported answer was '{d['answer']}'.",
                source_module="assessment",
                severity=severity,
                evidence=f"Question {q_id} answered '{d['answer']}' during governance assessment. Notes: {d['notes']}",
                business_impact=why_it_matters,
                recommended_action=f"Formulate automotive remediation plan: {d['question_text']}",
                status="Open"
            )
            db.add(risk)

    db.commit()

    # Generate recommendations for App 9
    recs = generate_and_save_recommendations(db, application_id=app_obj.id, assessment_id=assessment.id)
    print("Generated recommendations count for App 9:", len(recs))

    # Verify demo app 1 remains completely separate and untouched
    demo_assessments = db.query(Assessment).filter(Assessment.application_id == 1).all()
    print("Demo app 1 assessments count:", len(demo_assessments))
    assert len(demo_assessments) > 0, "Demo assessments should remain intact"

    db.close()
    print("SUCCESSFULLY SEEDED SUNTECH BASELINE ASSESSMENT!")

if __name__ == "__main__":
    seed_suntech()
