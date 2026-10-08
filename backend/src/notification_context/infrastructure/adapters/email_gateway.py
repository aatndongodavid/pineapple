# backend/src/notification_context/infrastructure/adapters/email_gateway.py

import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from shared_kernel.config import settings
from notification_context.infrastructure.persistence.models import NotificationDeliveryModel
from notification_context.domain.value_objects import NotificationChannel, DeliveryStatus


class EmailGatewayAdapter:
    """
    Adaptateur pour le canal E-mail avec support des gabarits HTML/texte,
    en-têtes RFC 8058 (List-Unsubscribe en un clic) et connexion SMTP/MailHog.
    """

    def __init__(self, smtp_host: str = None, smtp_port: int = None):
        self.smtp_host = smtp_host or settings.MAILHOG_HOST or "localhost"
        self.smtp_port = smtp_port or int(settings.MAILHOG_PORT or 1025)

    @staticmethod
    def generate_unsubscribe_token(user_id: uuid.UUID, tenant_id: uuid.UUID, category: str) -> str:
        """Génère un jeton JWT signé pour le désabonnement e-mail en 1 clic sans authentification requise."""
        claims = {
            "sub": str(user_id),
            "tid": str(tenant_id),
            "cat": category,
            "action": "unsubscribe",
        }
        return jwt.encode(claims, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def verify_unsubscribe_token(token: str) -> dict:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        tenant_id: Optional[uuid.UUID] = None,
        category: str = "INFO",
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Envoie un e-mail via le serveur SMTP/MailHog.
        Retourne (success, provider_name, provider_ref_or_error).
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = "no-reply@pineapple.campus"
        msg["To"] = to_email

        # Ajout des en-têtes RFC 8058 One-Click Unsubscribe
        if user_id and tenant_id:
            token = self.generate_unsubscribe_token(user_id, tenant_id, category)
            unsub_url = f"http://localhost:8000/api/v1/notifications/unsubscribe?token={token}"
            msg["List-Unsubscribe"] = f"<{unsub_url}>"
            msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        if body_html:
            msg.attach(MIMEText(body_html, "html", "utf-8"))

        try:
            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=5) as server:
                server.send_message(msg)
            return True, "SMTP/MailHog", f"msg_{uuid.uuid4().hex[:8]}"
        except Exception as exc:
            return False, "SMTP/MailHog", str(exc)
