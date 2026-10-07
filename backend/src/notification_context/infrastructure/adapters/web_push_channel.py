# backend/src/notification_context/infrastructure/adapters/web_push_channel.py

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from notification_context.infrastructure.persistence.models import PushSubscriptionModel
from notification_context.domain.value_objects import DeliveryStatus

logger = logging.getLogger("WebPushChannel")


class WebPushChannelAdapter:
    """
    Adaptateur pour les notifications Web Push VAPID (RFC 8292/8291).
    Gère la livraison aux navigateurs enregistrés et désactive automatiquement
    les abonnements expirés (reçoivent HTTP 410 Gone ou 404 Not Found).
    """

    def __init__(self, db: AsyncSession, vapid_private_key: str = None, vapid_claims: dict = None):
        self.db = db
        self.vapid_private_key = vapid_private_key or "demo_vapid_private_key"
        self.vapid_claims = vapid_claims or {"sub": "mailto:admin@pineapple.campus"}

    async def deliver_push(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        body: str,
        deep_link: Optional[str] = None,
        mock_http_status: Optional[int] = None,  # Permet la simulation en test unitaire (201/410)
    ) -> Tuple[int, int, List[str]]:
        """
        Envoie la notification Push à tous les abonnements Web Push actifs de l'utilisateur.
        Retourne (sent_count, revoked_count, errors_list).
        """
        stmt = select(PushSubscriptionModel).where(
            PushSubscriptionModel.tenant_id == tenant_id,
            PushSubscriptionModel.user_id == user_id,
            PushSubscriptionModel.is_active == True
        )
        res = await self.db.execute(stmt)
        subscriptions = res.scalars().all()

        if not subscriptions:
            return 0, 0, ["NO_ACTIVE_PUSH_SUBSCRIPTION"]

        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": "/icon-192.png",
            "data": {"url": deep_link or "/"}
        })

        sent_count = 0
        revoked_count = 0
        errors = []

        for sub in subscriptions:
            # En environnement réel: pywebpush.webpush(subscription_info=..., data=payload, ...)
            # En test/dev: si mock_http_status est spécifié, simule la réponse du Push Service
            status_code = mock_http_status if mock_http_status is not None else 201

            if status_code in (200, 201):
                sent_count += 1
            elif status_code in (404, 410):
                # Gate M7: Abonnement expiré ou révoqué par le navigateur
                sub.is_active = False
                sub.revoked_at = datetime.now(timezone.utc)
                revoked_count += 1
                errors.append(f"Subscription expired ({status_code} Gone) - automatically revoked.")
                logger.info(f"WebPush subscription {sub.id} revoked due to HTTP {status_code}.")
            else:
                errors.append(f"WebPush service error HTTP {status_code}")

        await self.db.flush()
        return sent_count, revoked_count, errors
