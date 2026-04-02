import os
import ssl
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

BRAND = "Hyt Orbis World Builder"
BRAND_URL = "https://hytorbisworldbuilder.com"
BRAND_COLOR = "#10b981"


def _get_smtp_config():
    return {
        "host": os.environ.get("SMTP_HOST"),
        "port": int(os.environ.get("SMTP_PORT", "465")),
        "user": os.environ.get("SMTP_USER"),
        "password": os.environ.get("SMTP_PASSWORD"),
        "from_addr": os.environ.get("SMTP_FROM", os.environ.get("SMTP_USER", "")),
    }


def _send_email(to_email: str, subject: str, html_body: str):
    cfg = _get_smtp_config()
    if not all([cfg["host"], cfg["user"], cfg["password"]]):
        logger.warning("SMTP not configured, skipping email")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{BRAND} <{cfg['from_addr']}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=context) as server:
            server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["from_addr"], to_email, msg.as_string())
        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def _base_template(content: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f1117;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0f1117;padding:40px 20px;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background:#1a1d27;border-radius:16px;border:1px solid #2a2d3a;overflow:hidden;">
<tr><td style="padding:32px 40px 24px;text-align:center;border-bottom:1px solid #2a2d3a;">
<h1 style="margin:0;color:{BRAND_COLOR};font-size:22px;font-weight:800;letter-spacing:-0.5px;">{BRAND}</h1>
</td></tr>
<tr><td style="padding:32px 40px;">
{content}
</td></tr>
<tr><td style="padding:20px 40px;text-align:center;border-top:1px solid #2a2d3a;">
<p style="margin:0;color:#6b7280;font-size:12px;">
<a href="{BRAND_URL}" style="color:{BRAND_COLOR};text-decoration:none;">{BRAND_URL}</a>
</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def send_welcome_email(to_email: str, name: str):
    content = f"""
    <h2 style="margin:0 0 16px;color:#f3f4f6;font-size:20px;">Welcome, {name}!</h2>
    <p style="color:#d1d5db;font-size:15px;line-height:1.6;margin:0 0 20px;">
      Your account has been created. You're now ready to start building incredible game worlds.
    </p>
    <p style="color:#d1d5db;font-size:15px;line-height:1.6;margin:0 0 24px;">
      With your Explorer plan, you can create up to 5 worlds, use templates, and export in multiple formats.
      Upgrade anytime to unlock AI-powered generation and real-time collaboration.
    </p>
    <table cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr><td>
    <a href="{BRAND_URL}" style="display:inline-block;background:{BRAND_COLOR};color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">
      Start Building
    </a>
    </td></tr></table>
    """
    _send_email(to_email, f"Welcome to {BRAND}!", _base_template(content))


def send_subscription_upgraded_email(to_email: str, name: str, plan_name: str, amount: str):
    content = f"""
    <h2 style="margin:0 0 16px;color:#f3f4f6;font-size:20px;">Plan Upgraded!</h2>
    <p style="color:#d1d5db;font-size:15px;line-height:1.6;margin:0 0 20px;">
      Hey {name}, your subscription has been upgraded to the <strong style="color:{BRAND_COLOR};">{plan_name} Plan</strong> (${amount}/month).
    </p>
    <p style="color:#d1d5db;font-size:15px;line-height:1.6;margin:0 0 12px;">You now have access to:</p>
    <ul style="color:#d1d5db;font-size:14px;line-height:1.8;margin:0 0 24px;padding-left:20px;">
      <li>AI-powered world generation</li>
      <li>Real-time collaboration</li>
      <li>Version history</li>
      <li>All export formats</li>
      {"<li>Analytics dashboard</li><li>Priority support</li>" if plan_name == "Developer" else ""}
    </ul>
    <table cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr><td>
    <a href="{BRAND_URL}" style="display:inline-block;background:{BRAND_COLOR};color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">
      Go to World Builder
    </a>
    </td></tr></table>
    """
    _send_email(to_email, f"Your {plan_name} Plan is Active!", _base_template(content))


def send_subscription_cancelled_email(to_email: str, name: str):
    content = f"""
    <h2 style="margin:0 0 16px;color:#f3f4f6;font-size:20px;">Subscription Cancelled</h2>
    <p style="color:#d1d5db;font-size:15px;line-height:1.6;margin:0 0 20px;">
      Hey {name}, your subscription has been cancelled. You've been moved to the Explorer (Free) plan.
    </p>
    <p style="color:#d1d5db;font-size:15px;line-height:1.6;margin:0 0 20px;">
      You'll still have access to your existing worlds, but AI generation and collaboration features are now locked.
    </p>
    <p style="color:#9ca3af;font-size:14px;line-height:1.6;margin:0 0 24px;">
      Changed your mind? You can re-subscribe anytime from your account.
    </p>
    <table cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr><td>
    <a href="{BRAND_URL}" style="display:inline-block;background:#374151;color:#f3f4f6;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">
      View Plans
    </a>
    </td></tr></table>
    """
    _send_email(to_email, "Your subscription has been cancelled", _base_template(content))


def send_payment_failed_email(to_email: str, name: str, plan_name: str):
    content = f"""
    <h2 style="margin:0 0 16px;color:#f3f4f6;font-size:20px;">Payment Issue</h2>
    <p style="color:#d1d5db;font-size:15px;line-height:1.6;margin:0 0 20px;">
      Hey {name}, we had trouble processing your payment for the <strong>{plan_name} Plan</strong>.
    </p>
    <p style="color:#d1d5db;font-size:15px;line-height:1.6;margin:0 0 24px;">
      Please update your payment method or try again. If the issue persists, contact us at
      <a href="mailto:support@hytorbis.com" style="color:{BRAND_COLOR};text-decoration:none;">support@hytorbis.com</a>.
    </p>
    <table cellpadding="0" cellspacing="0" style="margin:0 auto;"><tr><td>
    <a href="{BRAND_URL}" style="display:inline-block;background:{BRAND_COLOR};color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">
      Update Payment
    </a>
    </td></tr></table>
    """
    _send_email(to_email, "Payment issue with your subscription", _base_template(content))
