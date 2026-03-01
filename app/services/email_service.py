import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    async def send_invite_email(self, to_email: str, invite_token: str) -> bool:
        try:
            if settings.ENV == "development" and settings.EMAIL_OVERRIDE_TO:
                recipient = settings.EMAIL_OVERRIDE_TO
            else:
                recipient = to_email

            invite_link = f"{settings.FRONTEND_URL}/set-password?token={invite_token}"
            html_content = self._build_invite_html(invite_link)

            payload = {
                "from": settings.EMAIL_FROM,
                "to": [recipient],
                "subject": "You're invited to Digital Workspace",
                "html": html_content
            }

            headers = {
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )

            if response.status_code not in (200, 201):
                logger.error("Failed to send email to %s. Resend API responded with status %s", to_email, response.status_code)
                return False

            logger.info("Invite email sent successfully to %s", to_email)
            return True

        except Exception:
            logger.exception("Exception occurred while sending invite email to %s", to_email)
            return False

    def _build_invite_html(self, invite_link: str) -> str:
        return f"""\
<html>
<body style="font-family: Arial, sans-serif; color: #333; max-width: 560px; margin: auto; padding: 20px;">
  <h2 style="color: #1a73e8;">Welcome to Digital Workspace</h2>
  <p>You have been invited to the platform. Please set your password to get started.</p>
  <p style="margin: 24px 0;">
    <a href="{invite_link}"
       style="background: #1a73e8; color: #fff; padding: 12px 24px;
              border-radius: 6px; text-decoration: none; font-weight: bold; display: inline-block;">
      Set Your Password
    </a>
  </p>
  <p style="font-size: 13px; color: #888;">
    Fallback link: <a href="{invite_link}" style="color: #1a73e8;">{invite_link}</a><br><br>
    This link will expire in 24 hours.<br>
    If you did not expect this email, you can safely ignore it.
  </p>
</body>
</html>"""
