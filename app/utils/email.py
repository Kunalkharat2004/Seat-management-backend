"""
Async email utility for sending invite emails.

In development mode the invite link is printed to the console.
In production mode the email is sent via SMTP with STARTTLS.

This module contains **no** business logic — only email delivery.
"""

import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_invite_email(to_email: str, token: str) -> None:
    """Send a password-setup invite link to *to_email*.

    Parameters
    ----------
    to_email : str
        Recipient email address.
    token : str
        Raw (unhashed) invite token to embed in the link.
    """
    invite_link = f"{settings.INVITE_BASE_URL}/set-password?token={token}"

    # ── Development mode: console only ────────────────────────────
    if settings.APP_ENV == "development":
        print(
            f"\n"
            f"╔══════════════════════════════════════════════════════╗\n"
            f"║            📧  INVITE EMAIL (dev mode)              ║\n"
            f"╠══════════════════════════════════════════════════════╣\n"
            f"║  To:   {to_email:<44} ║\n"
            f"║  Link: {invite_link:<44} ║\n"
            f"╚══════════════════════════════════════════════════════╝"
        )
        return

    # ── Production mode: send via SMTP ────────────────────────────
    msg = _build_message(to_email, invite_link)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=True,
        )
        logger.info("Invite email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send invite email to %s", to_email)


# ── Helpers (private) ─────────────────────────────────────────────

def _build_message(to_email: str, invite_link: str) -> EmailMessage:
    """Construct a multipart plain-text + HTML invite email."""
    msg = EmailMessage()
    msg["Subject"] = "You're invited – Set your password"
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email

    # Plain-text body
    plain = (
        "You have been invited to the Digital Workspace Management platform.\n\n"
        "Please set your password by visiting the link below:\n\n"
        f"  {invite_link}\n\n"
        "This link will expire in 24 hours.\n\n"
        "If you did not expect this email, you can safely ignore it."
    )
    msg.set_content(plain)

    # HTML body
    html = f"""\
<html>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 560px; margin: auto;">
  <h2 style="color: #1a73e8;">Welcome to Digital Workspace Management</h2>
  <p>You have been invited to the platform. Please set your password to get started.</p>
  <p style="margin: 24px 0;">
    <a href="{invite_link}"
       style="background: #1a73e8; color: #fff; padding: 12px 24px;
              border-radius: 6px; text-decoration: none; font-weight: bold;">
      Set Your Password
    </a>
  </p>
  <p style="font-size: 13px; color: #888;">
    This link will expire in 24 hours.<br>
    If you did not expect this email, you can safely ignore it.
  </p>
</body>
</html>"""
    msg.add_alternative(html, subtype="html")

    return msg
