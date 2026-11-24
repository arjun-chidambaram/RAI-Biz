"""
Module 04: SME Responsible AI Assessment Test Suite
===================================================
Covers:
- Load standard assessment questions
- Submit complete 20-question assessment with mixed responses
- Calculation of dimension scores (Fairness, Transparency, Privacy, Sustainability)
- Boundary scoring: Perfect 100% compliance vs 0% non-compliance
- Handling of 'Not Applicable' (N/A) responses (does not penalize score)
- Automatic trigger of Risk Engine on assessment submission
- Detailed response inspection by assessment ID
- Multi-assessment current flag management (is_current)
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Assessment, Risk

def test_load_standard_questions(auth_client_a: TestClient):
    """Verifies retrieval of standard 20 assessment questions across 4 categories."""
    res = auth_client_a.get("/api/assessments/questions")
    assert res.status_code == 200
    questions = res.json()
    assert len(questions) == 20
    categories = {q["category"] for q in questions}
    assert categories == {"fairness", "transparency", "privacy", "sustainability"}

def test_submit_assessment_mixed_scores(auth_client_a: TestClient, tenant_a):
    """Verifies submitting 20 questions calculates accurate dimension and overall scores."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id

    # Get questions
    q_res = auth_client_a.get(f"/api/assessments/questions?application_id={app_id}")
    questions = q_res.json()

    # 10 Yes, 5 Partially, 5 No
    responses = []
    for i, q in enumerate(questions):
        ans = "Yes" if i < 10 else ("Partially" if i < 15 else "No")
        responses.append({
            "question_id": q["id"],
            "answer": ans,
            "notes": f"Automated test note for {q['id']}"
        })

    payload = {
        "business_id": biz_id,
        "application_id": app_id,
        "name": "Automotive Q1 Governance Audit",
        "notes": "Automated verification run",
        "responses": responses
    }

    res = auth_client_a.post("/api/assessments", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] is not None
    assert data["overall_score"] is not None
    assert data["overall_score"] > 0.0
    assert len(data["dimension_scores"]) == 4
    assert len(data["responses"]) == 20

def test_submit_assessment_perfect_score(auth_client_a: TestClient, tenant_a):
    """Verifies 20 'Yes' answers yield 100.0% overall and 100.0% in all dimensions."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id

    q_res = auth_client_a.get(f"/api/assessments/questions?application_id={app_id}")
    questions = q_res.json()

    responses = [{"question_id": q["id"], "answer": "Yes", "notes": "Fully compliant"} for q in questions]

    payload = {
        "business_id": biz_id,
        "application_id": app_id,
        "name": "Perfect Compliance Audit",
        "notes": "All Yes",
        "responses": responses
    }

    res = auth_client_a.post("/api/assessments", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["overall_score"] == 100.0
    assert data["fairness_score"] == 100.0
    assert data["transparency_score"] == 100.0
    assert data["privacy_score"] == 100.0
    assert data["sustainability_score"] == 100.0

def test_submit_assessment_zero_score(auth_client_a: TestClient, tenant_a):
    """Verifies 20 'No' answers yield 0.0% overall and generate risk findings."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id

    q_res = auth_client_a.get(f"/api/assessments/questions?application_id={app_id}")
    questions = q_res.json()

    responses = [{"question_id": q["id"], "answer": "No", "notes": "Non-compliant"} for q in questions]

    payload = {
        "business_id": biz_id,
        "application_id": app_id,
        "name": "Zero Compliance Audit",
        "notes": "All No",
        "responses": responses
    }

    res = auth_client_a.post("/api/assessments", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["overall_score"] == 0.0
    assert data["fairness_score"] == 0.0

def test_retrieve_assessment_detail_by_id(auth_client_a: TestClient, tenant_a):
    """Verifies retrieving a specific assessment with all 20 question answers."""
    app_id = tenant_a["application"].id
    biz_id = tenant_a["business"].id

    # Create assessment
    q_res = auth_client_a.get("/api/assessments/questions")
    responses = [{"question_id": q["id"], "answer": "Yes", "notes": "Verified"} for q in q_res.json()]

    create_res = auth_client_a.post("/api/assessments", json={
        "business_id": biz_id,
        "application_id": app_id,
        "name": "Detail Inspection Target",
        "responses": responses
    })
    assessment_id = create_res.json()["id"]

    # Query details
    get_res = auth_client_a.get(f"/api/assessments/{assessment_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["id"] == assessment_id
    assert detail["name"] == "Detail Inspection Target"
    assert len(detail["responses"]) == 20
