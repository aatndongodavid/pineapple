# backend/src/notification_context/domain/services/deduplication_engine.py

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from notification_context.infrastructure.persistence.models import NotificationModel
from notification_context.domain.value_objects import NotificationChannel


class DeduplicationEngine:
    """
    Gère le dédoublonnage et le regroupement (Digest) des notifications
    sur une fenêtre temporelle courte (ex: 2 à 5 minutes).
    """

    @staticmethod
    def compute_dedup_key(event_type: str, user_id: uuid.UUID, channel: NotificationChannel, window_minutes: int = 2) -> str:
        now = datetime.now(timezone.utc)
        bucket = now.minute // window_minutes
        window_str = f"{now.strftime('%Y%m%d%H')}_{bucket}"
        return f"{event_type}:{user_id}:{channel.value}:{window_str}"

    @staticmethod
    async def is_duplicate(db: AsyncSession, dedup_key: str) -> bool:
        """Vérifie si une notification identique a déjà été créée sur cette fenêtre."""
        stmt = select(NotificationModel).where(NotificationModel.dedup_key == dedup_key)
        res = await db.execute(stmt)
        return res.scalars().first() is not None

    @staticmethod
    def digest_messages(event_type: str, count: int, sample_title: str) -> Tuple[str, str]:
        """Combine plusieurs événements similaires en 1 seul message récapitulatif."""
        title = f"Récapitulatif : {count} nouvelles annonces"
        body = f"Vous avez reçu {count} nouvelles notifications de type {event_type} (Dernière: {sample_title})."
        return title, body
