import smtplib
import logging
from email.mime.text import MIMEText
from app.config import SMTP_EMAIL, SMTP_APP_PASSWORD

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(to_email: str, subject: str, body: str) -> None:
    if not SMTP_EMAIL or not SMTP_APP_PASSWORD:
        raise RuntimeError("SMTP_EMAIL / SMTP_APP_PASSWORD not configured. Check your .env file.")

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = SMTP_EMAIL
    message["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
        server.sendmail(SMTP_EMAIL, [to_email], message.as_string())

    logger.info("Sent email to %s: %s", to_email, subject)