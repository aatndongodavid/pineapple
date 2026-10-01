# backend/src/shared_kernel/infrastructure/sms_gateway.py

import logging
from typing import List, Optional
from shared_kernel.domain.ports import SMSGatewayPort
from identity_context.domain.entities import User

logger = logging.getLogger("sms_gateway")

# Événements critiques autorisés à déclencher l'envoi de SMS (Partie T1)
ALLOWED_CRITICAL_SMS_EVENTS = {
    "ELECTION_CLOSING_SOON",   # Clôture imminente d'un vote
    "CERTIFICATION_RESULT",    # Validation ou rejet de certification
    "ACCOUNT_SECURITY_ALERT",  # Alerte de sécurité sur le compte
}


class MockSMSGateway(SMSGatewayPort):
    """
    Implémentation de test / développement du port SMSGatewayPort.
    Simule l'envoi de SMS en journalisant les messages.
    """

    def __init__(self):
        self.sent_messages: List[dict] = []

    async def send_sms(self, phone_number: str, message: str) -> bool:
        logger.info(f"[MOCK_SMS_GATEWAY] Envoi SMS vers {phone_number} : '{message}'")
        self.sent_messages.append({
            "phone_number": phone_number,
            "message": message,
        })
        return True


class AfricasTalkingSMSGateway(SMSGatewayPort):
    """Adaptateur stub pour l'agrégateur Africa's Talking (Production Afrique)."""

    def __init__(self, api_key: str = "", username: str = "sandbox"):
        self.api_key = api_key
        self.username = username

    async def send_sms(self, phone_number: str, message: str) -> bool:
        logger.info(f"[AFRICAS_TALKING_SMS] Envoi SMS vers {phone_number} : '{message}'")
        return True


class CriticalSMSNotificationService:
    """
    Service d'envoi de notifications SMS restreint aux événements critiques.
    Vérifie le consentement préalable et la présence du numéro de téléphone.
    """

    def __init__(self, sms_gateway: Optional[SMSGatewayPort] = None):
        self.sms_gateway = sms_gateway or MockSMSGateway()

    async def send_critical_alert(
        self, user: User, event_type: str, message_content: str
    ) -> bool:
        if event_type not in ALLOWED_CRITICAL_SMS_EVENTS:
            logger.warning(
                f"Tentative de SMS refusée : l'événement '{event_type}' n'est pas classé critique."
            )
            return False

        if not user.sms_consent:
            logger.info(
                f"SMS non envoyé à l'utilisateur {user.id} : consentement SMS non accordé."
            )
            return False

        if not user.phone_number:
            logger.warning(
                f"SMS non envoyé à l'utilisateur {user.id} : aucun numéro de téléphone renseigné."
            )
            return False

        formatted_message = f"[Pineapple Campus Alert] {message_content}"
        return await self.sms_gateway.send_sms(user.phone_number, formatted_message)
