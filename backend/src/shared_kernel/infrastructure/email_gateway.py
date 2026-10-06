import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import os

logger = logging.getLogger(__name__)


class EmailGateway:
    """Port d'envoi d'e-mails avec adaptateur SMTP MailHog pour le développement."""

    def __init__(self):
        self.host = os.getenv("MAILHOG_HOST", "localhost")
        self.port = int(os.getenv("MAILHOG_PORT", "1025"))

    async def send_email(self, to_email: str, subject: str, body_html: str, body_text: str = "") -> bool:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = "noreply@pineapple.campus"
        msg["To"] = to_email

        if body_text:
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        try:
            with smtplib.SMTP(self.host, self.port, timeout=3) as server:
                server.sendmail("noreply@pineapple.campus", [to_email], msg.as_string())
            logger.info(f"E-mail envoyé avec succès à {to_email} via MailHog ({self.host}:{self.port})")
            return True
        except Exception as e:
            logger.warning(f"Impossible d'envoyer l'e-mail via SMTP ({e}). Fallback en console:")
            logger.info(f"--- EMAIL TO: {to_email} | SUBJECT: {subject} ---\n{body_text or body_html}\n--- END EMAIL ---")
            return False


email_gateway = EmailGateway()
