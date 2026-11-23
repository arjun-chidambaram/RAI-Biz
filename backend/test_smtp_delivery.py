"""
RAI-Biz SMTP Email Delivery Diagnostic & Verification Tool.
Safely tests Gmail SMTP connectivity, authentication, TLS handshake,
and dispatches a real test verification email without exposing secrets.
"""

import os
import sys
import socket
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.config import settings

def mask_credential(val: str) -> str:
    if not val:
        return "<NOT CONFIGURED>"
    if len(val) <= 4:
        return "*" * len(val)
    return val[:2] + "*" * (len(val) - 4) + val[-2:]

def run_smtp_diagnostic(recipient_email: str = None) -> bool:
    print("=" * 65)
    print("RAI-Biz SMTP Email Delivery Diagnostic & Health Check")
    print("=" * 65)

    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    username = settings.SMTP_USERNAME
    password = settings.SMTP_PASSWORD
    from_addr = settings.EMAIL_FROM or username

    # Check 1: Environment & Settings Inspection
    print("\n[Step 1/5] Checking Configuration & Environment...")
    env_backend = backend_dir / ".env"
    env_root = backend_dir.parent / ".env"

    print(f"  - Backend .env exists: {env_backend.exists()} ({env_backend})")
    print(f"  - Root .env exists:    {env_root.exists()} ({env_root})")
    print(f"  - SMTP_HOST:           {host}")
    print(f"  - SMTP_PORT:           {port}")
    print(f"  - SMTP_USERNAME:       {username if username else '<MISSING>'}")
    print(f"  - SMTP_PASSWORD:       {mask_credential(password)}")
    print(f"  - EMAIL_FROM:          {from_addr if from_addr else '<MISSING>'}")

    if not username or not password:
        print("\n[ERROR] CRITICAL: SMTP credentials are not configured!")
        print("To fix this, create a '.env' file in either the project root or 'backend/' with:")
        print("  SMTP_HOST=smtp.gmail.com")
        print("  SMTP_PORT=587")
        print("  SMTP_USERNAME=your-actual-email@gmail.com")
        print("  SMTP_PASSWORD=your-16-char-app-password")
        print("  EMAIL_FROM=your-actual-email@gmail.com")
        print("\nNote: Generate an App Password at: https://myaccount.google.com/apppasswords")
        return False

    # Check 2: Network TCP Connectivity
    print("\n[Step 2/5] Testing TCP socket connection to mail server...")
    try:
        sock = socket.create_connection((host, port), timeout=10)
        sock.close()
        print(f"  [OK] Network connection to {host}:{port} established successfully.")
    except Exception as e:
        print(f"  [ERROR] Failed to connect to {host}:{port}: {e}")
        print("  Check network firewall or proxy settings blocking outbound port 587.")
        return False

    # Check 3: SMTP Protocol & STARTTLS Handshake
    print("\n[Step 3/5] Initializing SMTP protocol and STARTTLS encryption...")
    server = None
    try:
        server = smtplib.SMTP(host, port, timeout=15)
        ehlo_code, _ = server.ehlo()
        print(f"  - Initial EHLO status: {ehlo_code}")
        
        tls_code, tls_msg = server.starttls()
        print(f"  - STARTTLS status: {tls_code} ({tls_msg.decode('utf-8', errors='ignore').strip()})")
        
        ehlo2_code, _ = server.ehlo()
        print(f"  - Post-TLS EHLO status: {ehlo2_code}")
        print("  [OK] TLS encryption established successfully.")
    except Exception as e:
        print(f"  [ERROR] TLS handshake failed: {e}")
        if server:
            try:
                server.quit()
            except Exception:
                pass
        return False

    # Check 4: Authentication
    print("\n[Step 4/5] Testing SMTP Authentication...")
    try:
        auth_code, auth_msg = server.login(username, password)
        print(f"  - Auth response code: {auth_code}")
        print("  [OK] SMTP authentication SUCCEEDED! Valid credentials verified.")
    except smtplib.SMTPAuthenticationError as e:
        print(f"  [FAIL] SMTP Authentication FAILED: (code {e.smtp_code})")
        print("  Explanation: Google rejected your username or App Password.")
        print("  Remedies:")
        print("    1. Enable 2-Step Verification on your Google Account.")
        print("    2. Generate an App Password at https://myaccount.google.com/apppasswords")
        print("    3. Paste the 16-character password without spaces.")
        print("    4. Do not use your regular Google account login password.")
        try:
            server.quit()
        except Exception:
            pass
        return False
    except Exception as e:
        print(f"  [ERROR] Unexpected error during login: {e}")
        try:
            server.quit()
        except Exception:
            pass
        return False

    # Check 5: Real Email Delivery Test
    target_to = recipient_email or username
    print(f"\n[Step 5/5] Sending Real Test Verification Email to '{target_to}'...")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "RAI-Biz SMTP Delivery Test - Verification Confirmed"
        msg["From"] = from_addr
        msg["To"] = target_to

        text = (
            "Hello,\n\n"
            "This is a verified test email from your RAI-Biz Governance platform.\n"
            "If you are reading this, Gmail SMTP authentication and STARTTLS transmission\n"
            "are 100% operational and your email provider has accepted the message for delivery.\n\n"
            "— RAI-Biz Security Team\n"
        )
        msg.attach(MIMEText(text, "plain", "utf-8"))

        server.sendmail(from_addr, [target_to], msg.as_string())
        print(f"  [OK] Test email successfully ACCEPTED by Gmail SMTP for recipient: {target_to}")
        print("  Check your inbox (and Spam/Junk folder if not immediately visible).")
        server.quit()
        return True
    except smtplib.SMTPSenderRefused as e:
        print(f"  [ERROR] Sender address refused: {e}")
        print(f"  Ensure EMAIL_FROM matches '{username}'.")
    except smtplib.SMTPRecipientsRefused as e:
        print(f"  [ERROR] Recipient address refused: {e}")
    except Exception as e:
        print(f"  [ERROR] Delivery failed: {e}")
    finally:
        try:
            server.quit()
        except Exception:
            pass

    return False

if __name__ == "__main__":
    recipient = sys.argv[1] if len(sys.argv) > 1 else None
    success = run_smtp_diagnostic(recipient)
    sys.exit(0 if success else 1)
