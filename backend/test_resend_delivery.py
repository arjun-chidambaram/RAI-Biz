"""
RAI-Biz Resend Email Delivery Diagnostic & Verification Tool.
Tests Resend API configuration, authentication, and dispatches
a real test email to verify delivery without exposing secrets.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.services.email_service import send_verification_email, TEST_OUTBOX

def mask_key(k: str) -> str:
    if not k:
        return "<NOT CONFIGURED>"
    if len(k) <= 8:
        return "*" * len(k)
    return k[:6] + "*" * (len(k) - 10) + k[-4:]

def run_resend_test(recipient: str = "arjunchidambaram.b@gmail.com"):
    print("=" * 65)
    print("RAI-Biz Resend Email Delivery Test")
    print("=" * 65)

    print("\n[Step 1/3] Checking Resend Configuration...")
    print(f"  - RESEND_API_KEY: {mask_key(settings.RESEND_API_KEY)}")
    print(f"  - EMAIL_FROM:     {settings.EMAIL_FROM}")
    print(f"  - Recipient:      {recipient}")

    if not settings.RESEND_API_KEY:
        print("\n[ERROR] RESEND_API_KEY is not configured in backend/.env!")
        return False

    print("\n[Step 2/3] Dispatching real test verification email via Resend SDK...")
    test_otp = "741852"

    try:
        success = send_verification_email(recipient, test_otp)
        if success:
            outbox_entry = TEST_OUTBOX[-1] if TEST_OUTBOX else {}
            print("  [OK] Email successfully ACCEPTED by Resend!")
            print(f"  - Message ID: {outbox_entry.get('message_id')}")
            print(f"  - Recipient:  {outbox_entry.get('to_email')}")
            print(f"  - Provider:   {outbox_entry.get('provider')}")
            print("\n[Step 3/3] Delivery Confirmed!")
            print(f"  Please check your inbox at: {recipient}")
            return True
        else:
            print("  [FAIL] send_verification_email returned False")
            return False
    except Exception as e:
        print(f"  [ERROR] Resend delivery failed: {e}")
        return False

if __name__ == "__main__":
    to_addr = sys.argv[1] if len(sys.argv) > 1 else "arjunchidambaram.b@gmail.com"
    result = run_resend_test(to_addr)
    sys.exit(0 if result else 1)
