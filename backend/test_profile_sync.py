import sys
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_sync():
    print("--- 1. Authenticating as user 5 (arjunchidambaram.b@gmail.com) ---")
    sys.path.insert(0, ".")
    from app.database import SessionLocal
    from app.models import User, SessionRecord
    from app.services.auth_service import hash_token
    import secrets
    import datetime

    db = SessionLocal()
    user = db.query(User).filter(User.email == "arjunchidambaram.b@gmail.com").first()
    assert user is not None, "User 5 not found in DB"

    token = secrets.token_urlsafe(32)
    s_hash = hash_token(token)
    session_record = SessionRecord(
        user_id=user.id,
        session_hash=s_hash,
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=7)
    )
    db.add(session_record)
    db.commit()
    db.close()

    session = requests.Session()
    session.cookies.set("rai_biz_session", token)

    print("--- 2. Calling GET /api/auth/me ---")
    res_me = session.get(f"{BASE_URL}/api/auth/me")
    print("Status:", res_me.status_code)
    me_data = res_me.json()
    print("Authenticated:", me_data.get("authenticated"))
    print("Business:", me_data.get("business", {}).get("name"), "| Industry:", me_data.get("business", {}).get("industry"))
    print("Application:", me_data.get("application", {}).get("name"))
    assert me_data.get("business", {}).get("name") == "Suntech Enterprise", "Business name mismatch in /api/auth/me"
    assert me_data.get("business", {}).get("industry") == "Automotive Services", "Industry mismatch in /api/auth/me"
    assert me_data.get("application", {}).get("name") == "Smart Car Detailing Assistant", "Application mismatch in /api/auth/me"

    print("--- 3. Calling GET /api/dashboard ---")
    res_dash = session.get(f"{BASE_URL}/api/dashboard")
    print("Status:", res_dash.status_code)
    dash_data = res_dash.json()
    dash_biz = dash_data.get("business")
    dash_app = dash_data.get("application")
    print("Dashboard Business:", dash_biz.get("name"), "| Industry:", dash_biz.get("industry"))
    print("Dashboard Application:", dash_app.get("name"))
    assert dash_biz.get("name") == "Suntech Enterprise", "Dashboard business name mismatch"
    assert dash_biz.get("industry") == "Automotive Services", "Dashboard business industry mismatch"
    assert dash_app.get("name") == "Smart Car Detailing Assistant", "Dashboard application name mismatch"

    print("--- 4. Calling PUT /api/businesses/profile (Simulating Business Profile Save) ---")
    csrf_token = session.cookies.get("rai_biz_csrf") or "test_csrf"
    update_payload = {
        "name": "Suntech Enterprise",
        "industry": "Automotive Services",
        "size": "11-50",
        "location": "India",
        "description": "Premium automotive detailing and smart service diagnostics enterprise.",
        "contact_email": "contact@suntechenterprise.com",
        "app_name": "Smart Car Detailing Assistant",
        "purpose": "AI-assisted customer support, service recommendations, appointment management and business performance analysis",
        "business_function": "Automotive Detailing & Customer Service",
        "data_types": "Customer inquiries, service history, vehicle details, appointment logs",
        "automated_decision_impact": "High",
        "human_oversight": "None"
    }
    res_update = session.put(
        f"{BASE_URL}/api/businesses/profile",
        json=update_payload,
        headers={"X-CSRF-Token": csrf_token}
    )
    print("Update status:", res_update.status_code)
    print("Update response:", res_update.json())
    assert res_update.status_code == 200, f"Profile update failed: {res_update.text}"
    saved_biz = res_update.json().get("business")
    saved_app = res_update.json().get("application")
    assert saved_biz.get("name") == "Suntech Enterprise"
    assert saved_biz.get("industry") == "Automotive Services"
    assert saved_app.get("name") == "Smart Car Detailing Assistant"

    print("--- 5. Calling GET /api/businesses/profile (Simulating Refresh of Profile Page) ---")
    res_prof = session.get(f"{BASE_URL}/api/businesses/profile")
    print("Profile status:", res_prof.status_code)
    prof_data = res_prof.json()
    print("Refreshed Profile Business:", prof_data.get("business", {}).get("name"))
    print("Refreshed Profile Application:", prof_data.get("application", {}).get("name"))
    assert prof_data.get("business", {}).get("name") == "Suntech Enterprise"
    assert prof_data.get("application", {}).get("name") == "Smart Car Detailing Assistant"

    print("--- 6. Calling GET /api/dashboard again (Simulating Dashboard Page Load) ---")
    res_dash2 = session.get(f"{BASE_URL}/api/dashboard")
    dash2_data = res_dash2.json()
    print("Re-verified Dashboard Business:", dash2_data.get("business", {}).get("name"))
    print("Re-verified Dashboard Industry:", dash2_data.get("business", {}).get("industry"))
    print("Re-verified Dashboard Application:", dash2_data.get("application", {}).get("name"))
    assert dash2_data.get("business", {}).get("name") == "Suntech Enterprise"
    assert dash2_data.get("business", {}).get("industry") == "Automotive Services"
    assert dash2_data.get("application", {}).get("name") == "Smart Car Detailing Assistant"

    print("--- 7. Verifying Shared Demo Workspace (Business 1) is Intact ---")
    db = SessionLocal()
    from app.models import Business as BizModel, AIApplication as AppModel
    demo_biz = db.query(BizModel).filter(BizModel.id == 1).first()
    demo_app = db.query(AppModel).filter(AppModel.id == 1).first()
    print("Demo Business 1:", demo_biz.name, "| Industry:", demo_biz.industry)
    print("Demo App 1:", demo_app.name)
    assert demo_biz.name == "SmartHire Solutions Inc."
    assert demo_app.name == "ResumeMatcher AI"
    db.close()

    print("\nALL 7 TESTS PASSED SUCCESSFULLY! Synchronized across Profile, Dashboard, and Auth!")

if __name__ == "__main__":
    test_sync()
