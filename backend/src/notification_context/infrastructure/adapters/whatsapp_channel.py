# backend/src/notification_context/infrastructure/adapters/whatsapp_channel.py

import logging
import uuid
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from notification_context.domain.value_objects import NotificationCategory

logger = logging.getLogger("WhatsAppChannel")


class WhatsAppChannelAdapter:
    """
    Adaptateur pour le canal WhatsApp Business API (Cloud API Meta).
    Nécessite des modèles de messages pré-approuvés (HSM) et un opt-in explicite.
    """

    def __init__(self, db: AsyncSession, api_token: Optional[str] = None):
        self.db = db
        self.api_token = api_token or "demo_whatsapp_token"

    async def send_whatsapp_template(
        self,
        phone_number: str,
        template_name: str,
        language_code: str = "fr",
        parameters: Optional[list] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Envoie un message WhatsApp basé sur un modèle (HSM) pré-approuvé par Meta.
        """
        # TODO(externe): Validation du dépôt des modèles HSM auprès de Meta Business Manager
        logger.info(f"WhatsApp HSM '{template_name}' simulé à {phone_number[:6]}*** (Langue: {language_code})")
        return True, "MetaWhatsAppCloudAPI", f"wa_{uuid.uuid4().hex[:8]}"
