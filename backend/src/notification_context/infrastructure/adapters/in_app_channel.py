# backend/src/notification_context/infrastructure/adapters/in_app_channel.py

import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from notification_context.infrastructure.persistence.models import NotificationModel, NotificationDeliveryModel
from notification_context.domain.value_objects import NotificationCategory, NotificationChannel, DeliveryStatus
from shared_kernel.infrastructure.websocket_manager import notification_ws_manager


class InAppChannelAdapter:
    """
    Adaptateur pour la livraison In-App : persiste la notification en BDD
    et pousse immédiatement un message temps réel via WebSocket.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def deliver(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        category: NotificationCategory,
        criticality: NotificationCategory,
        title: str,
        body: str,
        deep_link: str = None,
        dedup_key: str = None,
    ) -> NotificationModel:
        notification = NotificationModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            category=category,
            criticality=criticality,
            title=title,
            body=body,
            deep_link=deep_link,
            dedup_key=dedup_key,
        )
        self.db.add(notification)

        delivery = NotificationDeliveryModel(
            id=uuid.uuid4(),
            notification_id=notification.id,
            channel=NotificationChannel.IN_APP,
            status=DeliveryStatus.DELIVERED,
            provider_name="InAppWebSocket",
            attempts=1,
        )
        self.db.add(delivery)
        await self.db.flush()

        # Push WebSocket temps réel
        payload = {
            "type": "NOTIFICATION_RECEIVED",
            "id": str(notification.id),
            "category": category.value,
            "title": title,
            "body": body,
            "deep_link": deep_link,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await notification_ws_manager.send_user_notification(str(tenant_id), str(user_id), payload)

        return notification
