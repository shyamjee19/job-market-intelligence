"""Email sending - real SMTP delivery when SMTP_HOST/SMTP_USER/SMTP_PASSWORD
are all set, otherwise logs the message instead (to notification_log via
the caller, and to the app log here) rather than pretending to send it.
Same "unconfigured -> degrade, don't crash" pattern as every other
optional integration in this project.
"""
import smtplib
from email.message import EmailMessage

from config.settings import settings
from utils.logger import logger

is_configured = bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def send_email(to_address: str, subject: str, body: str) -> bool:
    """Returns True if the email was actually sent, False if it was only
    logged. Never raises - a notification failure shouldn't take down
    whatever triggered it (e.g. the job-alert background task)."""
    if not is_configured:
        logger.info("[email:not-configured] to=%s subject=%r (would send if SMTP_* were set)", to_address, subject)
        return False

    message = EmailMessage()
    message["From"] = settings.EMAIL_FROM_ADDRESS
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        logger.info("[email:sent] to=%s subject=%r", to_address, subject)
        return True
    except Exception:
        logger.exception("[email:failed] to=%s subject=%r", to_address, subject)
        return False
