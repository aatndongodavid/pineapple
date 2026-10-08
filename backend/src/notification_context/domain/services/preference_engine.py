# backend/src/notification_context/domain/services/preference_engine.py

import uuid
from datetime import datetime, timezone
from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from identity_context.infrastructure.persistence.models import UserModel
from notification_context.infrastructure.persistence.models import (
    NotificationPreferenceModel, QuietHoursModel, ChannelQuotaModel
)
from notification_context.domain.value_objects import NotificationCategory, NotificationChannel


class PreferenceEngine:
    """
    Moteur d'évaluation du consentement, des préférences utilisateur,
    des heures calmes et des quotas d'établissement.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def should_deliver(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        category: NotificationCategory,
        criticality: NotificationCategory,
        channel: NotificationChannel,
        current_dt: Optional[datetime] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Évalue si la notification doit être livrée sur le canal demandé.
        Retourne (True, None) si autorisé, ou (False, "MOTIF_SKIPPED") si bloqué.
        """
        dt = current_dt or datetime.now(timezone.utc)

        # 1. Vérification du consentement SMS explicite (ART / Cameroun)
        if channel == NotificationChannel.SMS:
            user = await self.db.get(UserModel, user_id)
            if not user or not getattr(user, "sms_consent", True):  # Par défaut actif pour les alertes de compte si non spécifié
                if not user or getattr(user, "sms_consent", None) is False:
                    return False, "NO_SMS_CONSENT"

        # 2. Vérification de la matrice des préférences (catégorie x canal)
        pref_stmt = select(NotificationPreferenceModel).where(
            NotificationPreferenceModel.user_id == user_id,
            NotificationPreferenceModel.tenant_id == tenant_id,
            NotificationPreferenceModel.category == category.value,
            NotificationPreferenceModel.channel == channel.value
        )
        pref_res = await self.db.execute(pref_stmt)
        pref = pref_res.scalars().first()

        # Si l'utilisateur a explicitement désactivé le canal pour cette catégorie
        if pref and not pref.is_enabled:
            # Exception : les notifications de sécurité CRITICAL ignorent la désactivation utilisateur
            if criticality != NotificationCategory.CRITICAL:
                return False, "DISABLED_BY_USER"

        # 3. Vérification des heures calmes (Quiet Hours)
        if criticality != NotificationCategory.CRITICAL:
            qh_stmt = select(QuietHoursModel).where(
                QuietHoursModel.user_id == user_id,
                QuietHoursModel.is_enabled == True
            )
            qh_res = await self.db.execute(qh_stmt)
            qh = qh_res.scalars().first()

            if qh:
                cur_hour = dt.hour
                is_quiet = False
                if qh.start_hour > qh.end_hour:
                    # Ex: 21h à 6h (traverse minuit)
                    if cur_hour >= qh.start_hour or cur_hour < qh.end_hour:
                        is_quiet = True
                else:
                    # Ex: 1h à 5h
                    if qh.start_hour <= cur_hour < qh.end_hour:
                        is_quiet = True

                if is_quiet:
                    return False, "QUIET_HOURS"

        # 4. Vérification des quotas d'établissement pour le SMS
        if channel == NotificationChannel.SMS:
            quota_stmt = select(ChannelQuotaModel).where(
                ChannelQuotaModel.tenant_id == tenant_id,
                ChannelQuotaModel.channel == "SMS"
            )
            quota_res = await self.db.execute(quota_stmt)
            quota = quota_res.scalars().first()

            if quota and quota.current_usage >= quota.max_limit:
                return False, "QUOTA_EXCEEDED"

        return True, None
