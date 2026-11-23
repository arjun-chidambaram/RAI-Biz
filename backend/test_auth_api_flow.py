import requests
import secrets
import datetime
from app.database import SessionLocal
from app.models import User, SessionRecord
from app.services.auth_service import hash_token
from app.config import settings

BASE_URL = "http://localhost:8000"

def test_authenticated_flow():
    # 1. Generate session token for user_id=1 (Arjun / Suntech Enterprise)
    db = SessionLocal()
    token = secrets.token_urlsafe(32)
    session_hash = hash_token(token)
    now = datetime.datetime.utcnow()
    expires = now + datetime.timedelta(days=1)
    
    try:
        user = db.query(User).filter(User.id == 5).first()
        assert user is not None, "User ID 5 not found"
        
        session_rec = SessionRecord(
            user_id=user.id,
            session_hash=session_hash,
            expires_at=expires,
            created_at=now
        )
        db.add(session_rec)
        db.commit()
        print(f"Created active test session for {user.email}")
    finally:
        db.close()

    session = requests.Session()
    # Pass session token as cookie and authorization header
    session.cookies.set(settings.SESSION_COOKIE_NAME, token)
    headers = {
        "Authorization": f"Bearer {token}"
    }
    session.headers.update(headers)

    # 2. Check /api/auth/me
    r_me = session.get(f"{BASE_URL}/api/auth/me")
    assert r_me.status_code == 200, f"Expected 200, got {r_me.status_code}: {r_me.text}"
    me_data = r_me.json()
    assert me_data["authenticated"] is True
    print(f"\n1. /api/auth/me: User '{me_data['user']['email']}', Business '{me_data['business']['name']}' ({me_data['business']['industry']}), App '{me_data['application']['name']}'")

    # 3. Test questions for Suntech (application_id=9)
    r_auto = session.get(f"{BASE_URL}/api/assessments/questions?application_id=9")
    assert r_auto.status_code == 200, f"Expected 200, got {r_auto.status_code}: {r_auto.text}"
    q_auto = r_auto.json()
    assert len(q_auto) == 20
    print(f"\n2. Suntech Questions (Automotive): Total {len(q_auto)}")
    print(f"   - F1: {q_auto[0]['question_text']}")
    print(f"   - Required Evidence: {q_auto[0]['evidence_required']}")
    print(f"   - Severity: {q_auto[0]['risk_severity']}, Category: {q_auto[0]['risk_category']}")
    assert "vehicle" in q_auto[0]['question_text'].lower() or "detailing" in q_auto[0]['question_text'].lower() or "Smart Car Detailing Assistant" in q_auto[0]['question_text']

    # 4. Test questions for SmartHire (application_id=1, Demo Workspace)
    r_hr = session.get(f"{BASE_URL}/api/assessments/questions?application_id=1")
    assert r_hr.status_code == 200, f"Expected 200, got {r_hr.status_code}: {r_hr.text}"
    q_hr = r_hr.json()
    assert len(q_hr) == 20
    print(f"\n3. SmartHire Questions (Recruitment): Total {len(q_hr)}")
    print(f"   - F1: {q_hr[0]['question_text']}")
    assert "candidate" in q_hr[0]['question_text'].lower() or "resume" in q_hr[0]['question_text'].lower() or "ResumeMatcher AI" in q_hr[0]['question_text']

    # 5. Verify questions differ across industries
    assert q_auto[0]['question_text'] != q_hr[0]['question_text'], "Automotive and HR questions must NOT be identical!"
    print(f"\n4. [VERIFIED] Automotive and Recruitment question banks are domain-isolated and distinct!")

    # 6. Test dynamic generation endpoint
    r_gen = session.post(f"{BASE_URL}/api/assessments/generate-questions", json={
        "application_id": 9,
        "force_llm": False
    })
    assert r_gen.status_code == 200, f"Expected 200, got {r_gen.status_code}: {r_gen.text}"
    gen_data = r_gen.json()
    print(f"\n5. Dynamic Question Generation Endpoint: Generated for '{gen_data['business_name']}', Industry: '{gen_data['industry']}' ({gen_data['industry_key']})")
    print(f"   Engine: '{gen_data['generation_source']}', Total Questions: {gen_data['question_count']}")
    assert gen_data["question_count"] == 20
    assert gen_data["industry_key"] == "automotive_services"

    # 7. Test /api/assessments list
    r_list = session.get(f"{BASE_URL}/api/assessments?application_id=9")
    assert r_list.status_code == 200
    list_data = r_list.json()
    print(f"\n6. Assessments List for Suntech: {len(list_data)} runs found")
    if list_data:
        latest = list_data[0]
        print(f"   Latest: ID {latest['id']}, Score: {latest['overall_score']}, Industry: '{latest.get('industry')}', Version: '{latest.get('question_version')}'")
        assert latest.get("industry") == "Automotive Services"

    print("\nALL AUTHENTICATED END-TO-END TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_authenticated_flow()
