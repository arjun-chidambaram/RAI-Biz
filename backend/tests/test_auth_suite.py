import os
import sys
import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import User, EmailOTP, SessionRecord, Business, BusinessUser, AIApplication
from app.config import settings
from app.services.email_service import TEST_OUTBOX
from app.services.auth_service import hash_otp, _RATE_LIMIT_EMAIL, _RATE_LIMIT_IP

client = TestClient(app)

def test_full_auth_suite():
    print("=" * 60)
    print("RAI-Biz Authentication Integration Test Suite (14 Tests)")
    print("=" * 60)

    db = SessionLocal()
    results = {}

    try:
        # PRE-FLIGHT TEST: Missing credentials must be rejected with HTTP 400 and NO OTP committed
        print("\n--- Pre-Flight Check: Missing Email Credentials Rejection ---")
        orig_resend = settings.RESEND_API_KEY
        orig_user = settings.SMTP_USERNAME
        orig_pass = settings.SMTP_PASSWORD
        settings.RESEND_API_KEY = ""
        settings.SMTP_USERNAME = ""
        settings.SMTP_PASSWORD = ""
        missing_res = client.post("/api/auth/send-otp", json={"email": "unconfigured@test.com"})
        assert missing_res.status_code == 400, f"Expected 400, got {missing_res.status_code}"
        assert "Email delivery is not configured" in missing_res.json()["detail"]
        # Verify no OTP was committed in DB
        unconf_otp = db.query(EmailOTP).filter(EmailOTP.email == "unconfigured@test.com").first()
        assert unconf_otp is None, "Failed delivery must not commit an OTP"
        print("PASS: Unconfigured email provider rejected with HTTP 400 and no OTP committed.")

        # Restore Resend configuration with mock for fast regression isolation
        settings.RESEND_API_KEY = orig_resend or "re_test_dummy_key"
        settings.SMTP_USERNAME = orig_user
        settings.SMTP_PASSWORD = orig_pass

        with patch("resend.Emails.send", return_value={"id": "test-resend-id-12345"}):
            # TEST 14: Existing SmartHire demo data remains intact
            print("\n--- Test 14: Verify Existing SmartHire Demo Data Intact ---")
            demo_biz = db.query(Business).filter(Business.id == 1).first()
            assert demo_biz is not None, "Demo business ID 1 must exist"
            assert "SmartHire" in demo_biz.name, f"Expected SmartHire, got {demo_biz.name}"
            demo_app = db.query(AIApplication).filter(AIApplication.business_id == 1).first()
            assert demo_app is not None, "Demo application must exist"
            print(f"PASS: Demo business '{demo_biz.name}' and app '{demo_app.name}' intact.")
            results["14. Demo Data Intact"] = True

            # TEST 12: Unauthenticated users cannot access protected APIs
            print("\n--- Test 12: Unauthenticated Access Rejected ---")
            unauth_resp = client.get("/api/dashboard")
            assert unauth_resp.status_code == 401, f"Expected 401, got {unauth_resp.status_code}"
            assert "Authentication required" in unauth_resp.json()["detail"]
            print("PASS: Unauthenticated call to /api/dashboard returned 401 Unauthorized.")
            results["12. Unauthenticated Blocked"] = True

            # TEST 1 & 2: New user enters an email -> OTP delivered
            print("\n--- Test 1 & 2: New User OTP Request & Delivery ---")
            TEST_OUTBOX.clear()
            new_email = "new_executive@acme-corp.com"
            
            # Clean test state for this email
            db.query(EmailOTP).filter(EmailOTP.email == new_email).delete()
            user_rec = db.query(User).filter(User.email == new_email).first()
            if user_rec:
                db.query(BusinessUser).filter(BusinessUser.user_id == user_rec.id).delete()
                db.query(SessionRecord).filter(SessionRecord.user_id == user_rec.id).delete()
                db.delete(user_rec)
            db.commit()

            # Send OTP
            res = client.post("/api/auth/send-otp", json={"email": new_email})
            assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
            assert res.json()["success"] is True
            print(f"PASS (Test 1): OTP requested successfully for {new_email}.")
            results["1. New User OTP Request"] = True

            # Verify delivery in TEST_OUTBOX
            assert len(TEST_OUTBOX) > 0, "Email must be dispatched to outbox"
            latest_delivery = TEST_OUTBOX[-1]
            assert latest_delivery["to_email"] == new_email
            otp_code = latest_delivery["otp_code"]
            assert len(otp_code) == 6 and otp_code.isdigit(), f"Expected 6 digit OTP, got {otp_code}"
            print(f"PASS (Test 2): Email delivered with valid 6-digit OTP code.")
            results["2. OTP Delivered via Email"] = True

            # TEST 9: Resend Cooldown
            print("\n--- Test 9: Resend Cooldown (60 seconds) ---")
            cooldown_res = client.post("/api/auth/send-otp", json={"email": new_email})
            assert cooldown_res.status_code == 429, f"Expected 429 cooldown, got {cooldown_res.status_code}"
            print(f"PASS (Test 9): Cooldown enforced with HTTP 429: {cooldown_res.json()}")
            results["9. Resend Cooldown"] = True

            # TEST 6: Incorrect OTP Rejected
            print("\n--- Test 6: Incorrect OTP Rejected ---")
            bad_res = client.post("/api/auth/verify-otp", json={"email": new_email, "otp": "000000"})
            assert bad_res.status_code == 400, f"Expected 400, got {bad_res.status_code}"
            assert "attempt(s) remaining" in bad_res.json()["detail"]
            print(f"PASS (Test 6): Incorrect OTP rejected with remaining attempts count: {bad_res.json()['detail']}")
            results["6. Incorrect OTP Rejected"] = True

            # TEST 10: Maximum Attempt Limit Works
            print("\n--- Test 10: Maximum Attempt Limit (5 attempts lockout) ---")
            # 1 bad attempt already made in Test 6 (attempts=1).
            # Make attempts 2, 3, 4:
            for i in range(3):
                client.post("/api/auth/verify-otp", json={"email": new_email, "otp": "000000"})
            # 5th attempt: triggers lockout
            lockout_res = client.post("/api/auth/verify-otp", json={"email": new_email, "otp": "000000"})
            assert lockout_res.status_code == 400, f"Expected 400, got {lockout_res.status_code}"
            assert "exceeded" in lockout_res.json()["detail"].lower(), f"Expected 'exceeded' in detail, got: {lockout_res.json()['detail']}"
            print(f"PASS (Test 10): 5th attempt locked out OTP: {lockout_res.json()['detail']}")
            results["10. Maximum Attempts Lockout"] = True

            # Reset cooldown & request fresh OTP for Tests 3, 4, 7, 8
            db.query(EmailOTP).filter(EmailOTP.email == new_email).delete()
            db.commit()
            if new_email in _RATE_LIMIT_EMAIL:
                del _RATE_LIMIT_EMAIL[new_email]

            client.post("/api/auth/send-otp", json={"email": new_email})
            valid_otp = TEST_OUTBOX[-1]["otp_code"]

            # TEST 7: Expired OTP is rejected
            print("\n--- Test 7: Expired OTP Rejected ---")
            otp_rec = db.query(EmailOTP).filter(EmailOTP.email == new_email, EmailOTP.is_used == False).first()
            assert otp_rec is not None
            otp_rec.expires_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
            db.commit()

            expired_res = client.post("/api/auth/verify-otp", json={"email": new_email, "otp": valid_otp})
            assert expired_res.status_code == 400, f"Expected 400, got {expired_res.status_code}"
            assert "expired" in expired_res.json()["detail"].lower()
            print(f"PASS (Test 7): Expired OTP rejected: {expired_res.json()['detail']}")
            results["7. Expired OTP Rejected"] = True

            # Request another fresh OTP for account creation
            db.query(EmailOTP).filter(EmailOTP.email == new_email).delete()
            db.commit()
            client.post("/api/auth/send-otp", json={"email": new_email})
            good_otp = TEST_OUTBOX[-1]["otp_code"]

            # TEST 3: Correct OTP creates a verified account
            print("\n--- Test 3: Correct OTP Creates Verified Account ---")
            verify_res = client.post("/api/auth/verify-otp", json={"email": new_email, "otp": good_otp})
            assert verify_res.status_code == 200, f"Expected 200, got {verify_res.status_code}: {verify_res.text}"
            body = verify_res.json()
            assert body["authenticated"] is True
            assert body["user"]["email"] == new_email
            assert body["user"]["is_verified"] is True
            assert "rai_biz_session" in verify_res.cookies, "HttpOnly session cookie must be set"
            print(f"PASS (Test 3): User account created & verified: {body['user']['email']}")
            results["3. Account Created & Verified"] = True

            # TEST 4: User reaches existing dashboard with session
            print("\n--- Test 4: Dashboard Access with Authenticated Session ---")
            dash_res = client.get("/api/dashboard", cookies=verify_res.cookies)
            assert dash_res.status_code == 200, f"Expected 200, got {dash_res.status_code}: {dash_res.text}"
            dash_data = dash_res.json()
            assert "overall_governance_score" in dash_data
            print(f"PASS (Test 4): Dashboard reached. Active App: {dash_data['application']['name'] if dash_data['application'] else 'None'}")
            results["4. Dashboard Access Verified"] = True

            # TEST 8: Reused single-use OTP is rejected
            print("\n--- Test 8: Reused Single-Use OTP Rejected ---")
            reused_res = client.post("/api/auth/verify-otp", json={"email": new_email, "otp": good_otp})
            assert reused_res.status_code == 400, f"Expected 400, got {reused_res.status_code}"
            print(f"PASS (Test 8): Reused OTP rejected: {reused_res.json()['detail']}")
            results["8. Reused OTP Rejected"] = True

            # TEST 5: Returning user can log in
            print("\n--- Test 5: Returning User Login ---")
            db.query(EmailOTP).filter(EmailOTP.email == new_email).delete()
            db.commit()
            client.post("/api/auth/send-otp", json={"email": new_email})
            return_otp = TEST_OUTBOX[-1]["otp_code"]

            ret_res = client.post("/api/auth/verify-otp", json={"email": new_email, "otp": return_otp})
            assert ret_res.status_code == 200
            assert ret_res.json()["authenticated"] is True
            assert ret_res.json()["user"]["email"] == new_email
            print(f"PASS (Test 5): Returning user authenticated with updated session.")
            results["5. Returning User Login"] = True

            # TEST 11: Logout invalidates session
            print("\n--- Test 11: Logout Invalidates Session ---")
            logout_res = client.post("/api/auth/logout", cookies=ret_res.cookies)
            assert logout_res.status_code == 200

            # Attempt to access protected dashboard with old cookies
            after_logout_dash = client.get("/api/dashboard", cookies=ret_res.cookies)
            assert after_logout_dash.status_code == 401, f"Expected 401 after logout, got {after_logout_dash.status_code}"
            print("PASS (Test 11): Logout cleanly invalidated session and cookies.")
            results["11. Logout Invalidation"] = True

            # TEST 13: One user cannot access another user's business records
            print("\n--- Test 13: Multi-Tenant Business Isolation ---")
            # User A
            email_a = "user_a@enterprise-a.com"
            db.query(EmailOTP).filter(EmailOTP.email == email_a).delete()
            db.commit()
            client.post("/api/auth/send-otp", json={"email": email_a})
            otp_a = TEST_OUTBOX[-1]["otp_code"]
            res_a = client.post("/api/auth/verify-otp", json={"email": email_a, "otp": otp_a})
            cookies_a = res_a.cookies
            biz_a = res_a.json()["business"]

            # User B
            email_b = "user_b@enterprise-b.com"
            db.query(EmailOTP).filter(EmailOTP.email == email_b).delete()
            db.commit()
            client.post("/api/auth/send-otp", json={"email": email_b})
            otp_b = TEST_OUTBOX[-1]["otp_code"]
            res_b = client.post("/api/auth/verify-otp", json={"email": email_b, "otp": otp_b})
            cookies_b = res_b.cookies
            biz_b = res_b.json()["business"]

            assert biz_a["id"] != biz_b["id"], f"Businesses must be distinct: {biz_a['id']} vs {biz_b['id']}"

            # User A attempts to view User B's applications
            cross_res = client.get(f"/api/applications?business_id={biz_b['id']}", cookies=cookies_a)
            assert cross_res.status_code == 403, f"Expected 403 Forbidden for cross-tenant access, got {cross_res.status_code}"
            print(f"PASS (Test 13): Cross-tenant access blocked with HTTP 403: {cross_res.json()['detail']}")
            results["13. Tenant Isolation Enforced"] = True

        print("\n" + "=" * 60)
        print("ALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        for name, passed in results.items():
            print(f"  [x] {name}")

        return True

    finally:
        db.close()

if __name__ == "__main__":
    success = test_full_auth_suite()
    if not success:
        sys.exit(1)
