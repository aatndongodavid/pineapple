# backend/src/notification_context/domain/services/broadcast_service.py

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from notification_context.domain.value_objects import NotificationCategory, NotificationChannel, DeliveryStatus
from notification_context.infrastructure.persistence.models import OutboxEventModel, NotificationModel
from notification_context.domain.services.audience_resolver import AudienceResolver
from notification_context.domain.services.preference_engine import PreferenceEngine
from identity_context.infrastructure.persistence.models import MembershipModel
from identity_context.domain.value_objects import MembershipRole

logger = logging.getLogger("BroadcastService")

MAX_DELEGATE_DAILY_BROADCASTS = 5


class BroadcastService:
    """
    Service de diffusion (broadcast) d'annonces établissement et annonces de classe.
    Gère la vérification des quotas délégués (5/jour) et la mise en file Outbox transactional.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audience_resolver = AudienceResolver(db)
        self.preference_engine = PreferenceEngine(db)

    async def broadcast_to_class_group(
        self,
        tenant_id: uuid.UUID,
        author_id: uuid.UUID,
        class_group_id: uuid.UUID,
        title: str,
        body: str,
        category: NotificationCategory = NotificationCategory.IMPORTANT,
        criticality: NotificationCategory = NotificationCategory.IMPORTANT,
        deep_link: Optional[str] = None,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> Tuple[bool, int, str]:
        """
        Diffuse une annonce à un groupe-classe (délégué ou enseignant).
        Vérifie la limite de 5 annonces / jour pour l'auteur.
        Retourne (success, count_recipients, broadcast_ref_or_reason).
        """
        # 1. Quota délégué (max 5 diffusion / jour)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        daily_count_stmt = select(func.count(OutboxEventModel.id)).where(
            OutboxEventModel.tenant_id == tenant_id,
            OutboxEventModel.event_type == "CLASS_ANNOUNCEMENT_PUBLISHED",
            OutboxEventModel.created_at >= today_start,
        )
        res = await self.db.execute(daily_count_stmt)
        count_today = res.scalar_one() or 0
        if count_today >= MAX_DELEGATE_DAILY_BROADCASTS:
            return False, 0, "DAILY_DELEGATE_QUOTA_EXCEEDED"

        # 2. Résolution de l'audience (membres de la classe)
        recipient_ids = await self.audience_resolver.resolve_class_group_members(tenant_id, class_group_id)
        if not recipient_ids:
            return True, 0, "NO_RECIPIENTS_FOUND"

        # 3. Canaux cibles par défaut
        target_channels = channels or [NotificationChannel.IN_APP, NotificationChannel.PUSH]

        # 4. Envoi Outbox / Création Notification
        broadcast_ref = f"bcast_{uuid.uuid4().hex[:8]}"
        enqueued_count = 0

        for uid in recipient_ids:
            for ch in target_channels:
                allowed, reason = await self.preference_engine.should_deliver(
                    tenant_id=tenant_id,
                    user_id=uid,
                    category=category,
                    criticality=criticality,
                    channel=ch,
                )
                if allowed:
                    outbox = OutboxEventModel(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        event_type="CLASS_ANNOUNCEMENT_PUBLISHED",
                        payload={
                            "user_id": str(uid),
                            "category": category.value,
                            "criticality": criticality.value,
                            "channel": ch.value,
                            "title": title,
                            "body": body,
                            "deep_link": deep_link or f"/class/{class_group_id}",
                        },
                        status="PENDING",
                    )
                    self.db.add(outbox)
                    enqueued_count += 1

        await self.db.flush()
        logger.info(f"Broadcast classe {class_group_id}: {enqueued_count} outbox créés pour {len(recipient_ids)} étudiants")
        return True, len(recipient_ids), broadcast_ref

    async def broadcast_to_tenant(
        self,
        tenant_id: uuid.UUID,
        author_id: uuid.UUID,
        title: str,
        body: str,
        category: NotificationCategory = NotificationCategory.IMPORTANT,
        criticality: NotificationCategory = NotificationCategory.IMPORTANT,
        role_filter: Optional[MembershipRole] = None,
        deep_link: Optional[str] = None,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> Tuple[bool, int, str]:
        """
        Diffuse une annonce à tout l'établissement (Admin seulement).
        Retourne (success, count_recipients, broadcast_ref).
        """
        recipient_ids = await self.audience_resolver.resolve_tenant_users(tenant_id)
        if not recipient_ids:
            return True, 0, "NO_RECIPIENTS_FOUND"

        target_channels = channels or [NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.PUSH]
        broadcast_ref = f"admin_bcast_{uuid.uuid4().hex[:8]}"
        enqueued_count = 0

        for uid in recipient_ids:
            for ch in target_channels:
                allowed, reason = await self.preference_engine.should_deliver(
                    tenant_id=tenant_id,
                    user_id=uid,
                    category=category,
                    criticality=criticality,
                    channel=ch,
                )
                if allowed:
                    outbox = OutboxEventModel(
                        id=uuid.uuid4(),
                        tenant_id=tenant_id,
                        event_type="TENANT_ANNOUNCEMENT_PUBLISHED",
                        payload={
                            "user_id": str(uid),
                            "category": category.value,
                            "criticality": criticality.value,
                            "channel": ch.value,
                            "title": title,
                            "body": body,
                            "deep_link": deep_link or "/announcements",
                        },
                        status="PENDING",
                    )
                    self.db.add(outbox)
                    enqueued_count += 1

        await self.db.flush()
        logger.info(f"Broadcast tenant {tenant_id}: {enqueued_count} outbox créés pour {len(recipient_ids)} membres")
        return True, len(recipient_ids), broadcast_ref
