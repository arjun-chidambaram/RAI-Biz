import sys
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_assessment_customization():
    print("=== TEST 1: Suntech Enterprise Authentication & Session ===")
    sys.path.insert(0, ".")
    from app.database import SessionLocal
    from app.models import User, SessionRecord, Assessment, Business, AIApplication
    from app.services.auth_service import hash_token
    import secrets
    import datetime

    db = SessionLocal()
    user = db.query(User).filter(User.email == "arjunchidambaram.b@gmail.com").first()
    assert user is not None, "User not found"

    token = secrets.token_urlsafe(32)
    s_hash = hash_token(token)
    session_record = SessionRecord(
        user_id=user.id,
        session_hash=s_hash,
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    )
    db.add(session_record)
    db.commit()
    db.close()

    session = requests.Session()
    session.cookies.set("rai_biz_session", token)

    res_me = session.get(f"{BASE_URL}/api/auth/me")
    assert res_me.status_code == 200
    me_data = res_me.json()
    assert me_data["business"]["name"] == "Suntech Enterprise"
    assert me_data["application"]["name"] == "Smart Car Detailing Assistant"
    app_id = me_data["application"]["id"]
    print(f"[PASS] Authenticated user primary app is '{me_data['application']['name']}' (ID: {app_id})")

    print("\n=== TEST 2: Question Catalog Inspection ===")
    res_q = session.get(f"{BASE_URL}/api/assessments/questions")
    assert res_q.status_code == 200, f"Failed to get questions: {res_q.text}"
    questions = res_q.json()
    assert len(questions) == 20, f"Expected 20 questions, got {len(questions)}"
    
    dims = {"fairness": 0, "transparency": 0, "privacy": 0, "sustainability": 0}
    forbidden_terms = ["candidate datasets", "hiring or scoring", "applicant distributions", "rejected candidates", "job applicants", "wrongful termination", "sensitive candidate"]
    
    for q in questions:
        dims[q["category"]] += 1
        combined_text = (q["question_text"] + " " + q["guidance"] + " " + q["why_it_matters"]).lower()
        for term in forbidden_terms:
            assert term not in combined_text, f"Question {q['id']} still contains recruitment term '{term}'!"

    print("All 20 questions verified across 4 dimensions:", dims)
    assert all(count == 5 for count in dims.values()), "Each dimension must have exactly 5 questions"
    print("[PASS] Question Catalog is completely free of recruitment bias and has all 20 criteria.")

    print("\n=== TEST 3: Suntech Enterprise Assessment Inspection ===")
    res_suntech_assessments = session.get(f"{BASE_URL}/api/assessments?application_id={app_id}")
    assert res_suntech_assessments.status_code == 200
    s_assessments = res_suntech_assessments.json()
    assert len(s_assessments) > 0, "Suntech Enterprise should have an assessment"
    latest_suntech = s_assessments[0]
    
    print(f"Suntech Assessment Name: {latest_suntech['name']}")
    print(f"Overall Score: {latest_suntech['overall_score']} / 100")
    print(f"Fairness: {latest_suntech['fairness_score']}, Transparency: {latest_suntech['transparency_score']}, Privacy: {latest_suntech['privacy_score']}, Sustainability: {latest_suntech['sustainability_score']}")
    
    # Requirement 10: Do not automatically mark the business as governance safe
    assert latest_suntech["overall_score"] < 80.0, "Suntech should not be marked as governance safe (score < 80)"
    
    # Verify responses contain automotive car detailing evidence notes
    res_details = session.get(f"{BASE_URL}/api/assessments/{latest_suntech['id']}")
    assert res_details.status_code == 200
    detail_data = res_details.json()
    responses = detail_data["responses"]
    assert len(responses) == 20
    
    notes_sample = [r["notes"] for r in responses if r.get("notes")]
    notes_combined = " ".join(notes_sample).lower()
    
    automotive_keywords = ["vehicle", "detailing", "ceramic", "paint", "customer", "appointment", "booking"]
    matched_keywords = [kw for kw in automotive_keywords if kw in notes_combined]
    print(f"Matched automotive detailing keywords in evidence notes: {matched_keywords}")
    assert len(matched_keywords) >= 5, "Evidence notes must contain specific automotive detailing references"
    
    recruitment_keywords = ["applicant", "candidate", "resume", "hiring manager"]
    for rkw in recruitment_keywords:
        assert rkw not in notes_combined, f"Suntech notes must not contain recruitment keyword '{rkw}'"

    print("[PASS] Suntech Enterprise assessment notes are 100% specific to automotive services and car detailing!")

    print("\n=== TEST 4: Shared Demo Workspace Isolation Check ===")
    res_demo_assessments = session.get(f"{BASE_URL}/api/assessments?application_id=1")
    assert res_demo_assessments.status_code == 200
    demo_assessments = res_demo_assessments.json()
    assert len(demo_assessments) > 0, "Demo assessments must exist"
    
    res_demo_details = session.get(f"{BASE_URL}/api/assessments/{demo_assessments[0]['id']}")
    assert res_demo_details.status_code == 200
    demo_detail = res_demo_details.json()
    demo_notes_combined = " ".join([r["notes"] for r in demo_detail["responses"] if r.get("notes")]).lower()
    
    # Demo workspace MUST preserve its recruitment demo notes
    assert "resume" in demo_notes_combined or "applicant" in demo_notes_combined or "candidate" in demo_notes_combined, "Demo workspace must preserve recruitment context"
    assert latest_suntech["id"] != demo_detail["id"], "Suntech assessment ID and Demo assessment ID must be distinct"
    assert latest_suntech["application_id"] != demo_detail["application_id"], "Application IDs must be distinct"
    print(f"[PASS] Shared Demo Workspace (App ID 1) is completely preserved and isolated from Suntech (App ID {app_id})!")

    print("\n=== TEST 5: Scoring Logic & Persistence on Update ===")
    csrf_token = session.cookies.get("rai_biz_csrf") or "test_csrf"
    
    # Simulate user changing F1 from Partially to Yes (score increases from 50 to 100 on F1)
    updated_responses = []
    for r in detail_data["responses"]:
        if r["question_id"] == "F1":
            updated_responses.append({
                "question_id": "F1",
                "answer": "Yes",
                "notes": "Implemented automated demographic parity and vehicle tier fairness testing pre-deployment."
            })
        else:
            updated_responses.append({
                "question_id": r["question_id"],
                "answer": r["answer"],
                "notes": r["notes"]
            })

    submit_payload = {
        "business_id": latest_suntech["business_id"],
        "application_id": app_id,
        "name": "Suntech Enterprise Updated Audit (Post-Remediation)",
        "notes": "Updated after deploying pre-deployment bias testing.",
        "responses": updated_responses
    }

    res_submit = session.post(
        f"{BASE_URL}/api/assessments",
        json=submit_payload,
        headers={"X-CSRF-Token": csrf_token}
    )
    assert res_submit.status_code == 200, f"Submit failed: {res_submit.text}"
    submit_res = res_submit.json()
    
    # In F1: Yes=100, F2: No=0, F3: Partially=50, F4: Partially=50, F5: No=0 -> Fairness = (100+0+50+50+0)/5 = 40.0
    # Other dimensions: Transparency = 40.0, Privacy = 30.0, Sustainability = 20.0
    # Overall score = (40 + 40 + 30 + 20) / 4 = 32.5
    print("New Fairness Score:", submit_res["fairness_score"])
    print("New Overall Score:", submit_res["overall_score"])
    assert submit_res["fairness_score"] == 40.0, f"Expected Fairness 40.0, got {submit_res['fairness_score']}"
    assert submit_res["overall_score"] == 32.5, f"Expected Overall 32.5, got {submit_res['overall_score']}"

    # Verify persistence by re-querying
    res_recheck = session.get(f"{BASE_URL}/api/assessments?application_id={app_id}")
    latest_recheck = res_recheck.json()[0]
    assert latest_recheck["name"] == "Suntech Enterprise Updated Audit (Post-Remediation)"
    assert latest_recheck["overall_score"] == 32.5
    print("[PASS] Scoring logic and persistence verified!")

    print("\n=== TEST 6: Overview Dashboard Sync ===")
    res_dash = session.get(f"{BASE_URL}/api/dashboard")
    assert res_dash.status_code == 200
    dash_data = res_dash.json()
    assert dash_data["business"]["name"] == "Suntech Enterprise"
    assert dash_data["application"]["name"] == "Smart Car Detailing Assistant"
    assert dash_data["overall_governance_score"] == 32.5
    assert dash_data["fairness_score"] == 40.0
    print(f"[PASS] Dashboard is in sync: {dash_data['business']['name']} - {dash_data['application']['name']} (Overall: {dash_data['overall_governance_score']}/100)")

    print("\nALL 6 COMPREHENSIVE TESTS PASSED! Suntech Enterprise Responsible AI Assessment is fully customized and verified.")

if __name__ == "__main__":
    test_assessment_customization()
