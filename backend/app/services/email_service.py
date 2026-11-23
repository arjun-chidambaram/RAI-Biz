import os
import smtplib
import socket
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any, List
import resend
from ..config import settings

logger = logging.getLogger("rai_biz.email")

# In-memory record of successfully accepted dispatches
TEST_OUTBOX: List[Dict[str, Any]] = []

def get_last_sent_test_email() -> Optional[Dict[str, Any]]:
    """Returns the most recent dispatched email metadata for diagnostics."""
    return TEST_OUTBOX[-1] if TEST_OUTBOX else None

def clear_test_outbox():
    TEST_OUTBOX.clear()

def build_email_content(to_email: str, otp_code: str) -> tuple[str, str, str]:
    subject = f"Your RAI-Biz Verification Code: {otp_code}"
    
    # Plain text version
    plain_text = f"""
Hello,

Your single-use verification code for the RAI-Biz Responsible AI Governance Platform is:

    {otp_code}

This code will expire in 5 minutes.

If you did not request this verification code, you can safely ignore this email.
Never share this code with anyone. RAI-Biz will never ask for your verification code.

— The RAI-Biz Governance Team
https://rai-biz.ai
"""

    # HTML version with enterprise RAI-Biz branding
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RAI-Biz Verification Code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; padding: 30px 15px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 520px; background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
          <!-- Header Banner -->
          <tr>
            <td style="background-color: #0B1528; padding: 32px 30px; text-align: center;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td align="center">
                    <div style="display: inline-block; width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #14b8a6, #0284c7); text-align: center; line-height: 44px; color: #ffffff; font-weight: bold; font-size: 20px; box-shadow: 0 4px 12px rgba(20, 184, 166, 0.3);">
                      🛡️
                    </div>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-top: 12px;">
                    <span style="color: #ffffff; font-size: 20px; font-weight: 800; letter-spacing: -0.5px;">RAI-Biz</span>
                    <span style="display: inline-block; background-color: rgba(20, 184, 166, 0.2); border: 1px solid rgba(20, 184, 166, 0.4); color: #2dd4bf; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; margin-left: 6px; vertical-align: middle;">SME</span>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-top: 4px;">
                    <span style="color: #94a3b8; font-size: 12px; font-weight: 500;">Responsible AI Governance & Risk Optimization</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body Content -->
          <tr>
            <td style="padding: 36px 30px 24px 30px;">
              <h1 style="color: #0f172a; font-size: 18px; font-weight: 700; margin: 0 0 12px 0;">Sign in to your RAI-Biz Workspace</h1>
              <p style="color: #475569; font-size: 14px; line-height: 1.6; margin: 0 0 24px 0;">
                Use the single-use 6-digit verification code below to verify your email address and access your SME Responsible AI dashboard.
              </p>

              <!-- OTP Code Highlight Box -->
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin: 0 0 24px 0;">
                <tr>
                  <td align="center" style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 12px; padding: 20px;">
                    <span style="font-family: 'Courier New', Courier, monospace; font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #0284c7; display: block; text-align: center;">
                      {otp_code}
                    </span>
                    <span style="display: block; color: #64748b; font-size: 11px; font-weight: 600; margin-top: 8px; text-transform: uppercase; letter-spacing: 0.5px;">
                      Expires in 5 minutes • Single-use code
                    </span>
                  </td>
                </tr>
              </table>

              <!-- Security Advice -->
              <div style="background-color: #fffbeb; border: 1px solid #fef3c7; border-radius: 8px; padding: 12px 16px; margin-bottom: 24px;">
                <p style="color: #92400e; font-size: 12px; line-height: 1.5; margin: 0;">
                  <strong>Security Note:</strong> If you did not initiate this request, someone may have entered your email address by mistake. Your account is secure and no action is needed. Never share this OTP with anyone.
                </p>
              </div>

              <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin: 0;">
                Best regards,<br>
                <strong style="color: #334155;">The RAI-Biz Governance & Compliance Team</strong>
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background-color: #f8fafc; border-top: 1px solid #f1f5f9; padding: 20px 30px; text-align: center;">
              <p style="color: #94a3b8; font-size: 11px; line-height: 1.5; margin: 0;">
                This is an automated system notification from RAI-Biz Platform.<br>
                Democratizing Responsible, Fair, and Sustainable AI for Small and Medium Enterprises.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return subject, plain_text, html_content

def send_verification_email(to_email: str, otp_code: str) -> bool:
    """
    Delivers verification email using Resend API (primary) or Gmail SMTP (secondary).
    CRITICAL: Does NOT simulate delivery. Raises explicit exceptions if credentials
    are missing or if the email provider rejects delivery.
    """
    normalized_to = to_email.strip().lower()
    subject, plain_text, html_content = build_email_content(normalized_to, otp_code)

    # 1. Primary Email Provider: Resend SDK
    resend_key = (settings.RESEND_API_KEY or "").strip()
    if resend_key:
        resend.api_key = resend_key
        email_from = (settings.EMAIL_FROM or "RAI-Biz <onboarding@resend.dev>").strip()

        params = {
            "from": email_from,
            "to": [normalized_to],
            "subject": subject,
            "html": html_content,
            "text": plain_text
        }

        try:
            response = resend.Emails.send(params)
            email_id = None
            if isinstance(response, dict):
                email_id = response.get("id")
            elif hasattr(response, "id"):
                email_id = getattr(response, "id")

            if not email_id:
                raise RuntimeError(f"Resend rejected email. No message ID returned in response: {response}")

            logger.info(f"Verification email successfully accepted by Resend (id={email_id}) for {normalized_to}")

            # Record in diagnostic outbox
            TEST_OUTBOX.append({
                "to_email": normalized_to,
                "otp_code": otp_code,
                "subject": subject,
                "provider": "resend",
                "message_id": email_id
            })

            return True

        except Exception as e:
            err_msg = str(e)
            logger.error(f"Resend delivery failed for {normalized_to}: {type(e).__name__}: {err_msg}")
            raise RuntimeError(f"Resend email delivery failed: {err_msg}")

    # 2. Secondary Email Provider: Gmail SMTP
    username = (settings.SMTP_USERNAME or "").strip()
    password = (settings.SMTP_PASSWORD or "").strip()

    if username and password:
        server = None
        sender = (settings.EMAIL_FROM or username).strip()
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = normalized_to
        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(username, password)
            server.sendmail(sender, [normalized_to], msg.as_string())

            logger.info(f"Verification email successfully accepted by SMTP for {normalized_to}")
            TEST_OUTBOX.append({
                "to_email": normalized_to,
                "otp_code": otp_code,
                "subject": subject,
                "provider": "smtp"
            })
            return True
        except Exception as e:
            logger.error(f"SMTP delivery failed for {normalized_to}: {str(e)}")
            raise RuntimeError(f"SMTP delivery failed: {str(e)}")
        finally:
            if server is not None:
                try:
                    server.quit()
                except Exception:
                    pass

    # 3. Neither Resend nor SMTP is configured
    logger.error(f"Cannot dispatch verification email to {normalized_to}: No email provider configured.")
    raise RuntimeError(
        "Email delivery is not configured. Missing RESEND_API_KEY in backend/.env. "
        "Please configure your Resend API key to enable email verification."
    )
