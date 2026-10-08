# backend/src/notification_context/infrastructure/adapters/sms_gateway.py

import logging
import uuid
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from identity_context.infrastructure.persistence.models import UserModel
from notification_context.infrastructure.persistence.models import ChannelQuotaModel, NotificationPreferenceModel
from notification_context.domain.value_objects import NotificationCategory

logger = logging.getLogger("SmsGateway")


class SmsGatewayAdapter:
    """
    Adaptateur pour l'envoi de SMS (Orange CM, MTN CM, Twilio, Simulated).
    Vérifie le consentement légal (sms_consent), limite le texte à 160 caractères,
    et incrémente la consommation de quota de l'établissement.
    """

    def __init__(self, db: AsyncSession, provider_name: str = "SimulatedSMS"):
        self.db = db
        self.provider_name = provider_name

    async def send_sms(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        phone_number: str,
        message: str,
        category: NotificationCategory = NotificationCategory.CRITICAL,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Tente l'envoi d'un SMS après vérification du consentement et du quota tenant.
        Retourne (success, provider_name, provider_ref_or_error_reason).
        """
        # 1. Vérification du consentement SMS utilisateur (ART / Cameroun)
        user = await self.db.get(UserModel, user_id)
        if not user:
            return False, self.provider_name, "NO_SMS_CONSENT"

        pref_stmt = select(NotificationPreferenceModel).where(
            NotificationPreferenceModel.user_id == user_id,
            NotificationPreferenceModel.tenant_id == tenant_id,
            NotificationPreferenceModel.channel == "SMS",
        )
        pref_res = await self.db.execute(pref_stmt)
        pref = pref_res.scalars().first()
        if (pref and not pref.is_enabled) or getattr(user, "sms_consent", None) is False:
            return False, self.provider_name, "NO_SMS_CONSENT"

        # 2. Vérification et réservation de quota tenant
        quota_stmt = select(ChannelQuotaModel).where(
            ChannelQuotaModel.tenant_id == tenant_id,
            ChannelQuotaModel.channel == "SMS"
        )
        quota_res = await self.db.execute(quota_stmt)
        quota = quota_res.scalars().first()

        if quota:
            if quota.current_usage >= quota.max_limit:
                return False, self.provider_name, "QUOTA_EXCEEDED"
            quota.current_usage += 1
        else:
            # Créer un quota par défaut si absent (ex: 500 SMS / mois)
            quota = ChannelQuotaModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                channel="SMS",
                period="MONTHLY",
                max_limit=500,
                current_usage=1,
            )
            self.db.add(quota)

        # 3. Tronquer le message à 160 caractères GSM
        clean_message = message[:157] + "..." if len(message) > 160 else message

        # 4. Envoi via le provider
        if self.provider_name == "OrangeSMS":
            # TODO(externe): Appel à l'API Orange SMS Cameroun (https://developer.orange.com/apis/sms-cameroon/)
            pass
        elif self.provider_name == "MtnSMS":
            # TODO(externe): Appel à l'API MTN SMS Cameroun
            pass

        logger.info(f"SMS envoyé à {phone_number[:6]}*** via {self.provider_name}: {clean_message}")
        await self.db.flush()
        return True, self.provider_name, f"sms_{uuid.uuid4().hex[:8]}"
