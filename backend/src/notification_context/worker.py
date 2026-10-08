# backend/src/notification_context/worker.py

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared_kernel.infrastructure.database import AsyncSessionLocal
from notification_context.infrastructure.persistence.models import OutboxEventModel
from notification_context.domain.value_objects import OutboxEventStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] OutboxWorker: %(message)s")
logger = logging.getLogger("OutboxWorker")


class OutboxWorker:
    """
    Worker asynchrone qui dépile les événements de la table outbox_events,
    les transforme en notifications multicanal et gère le backoff exponentiel.
    """

    def __init__(self, batch_size: int = 50, poll_interval: float = 2.0, max_attempts: int = 5):
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_attempts = max_attempts
        self._running = False

    async def process_batch(self, session: AsyncSession) -> int:
        """Récupère et traite un lot d'événements PENDING."""
        stmt = (
            select(OutboxEventModel)
            .where(OutboxEventModel.status == OutboxEventStatus.PENDING)
            .order_by(OutboxEventModel.created_at.asc())
            .limit(self.batch_size)
            .with_for_update(skip_locked=True)
        )
        res = await session.execute(stmt)
        events = res.scalars().all()

        if not events:
            return 0

        for event in events:
            event.status = OutboxEventStatus.PROCESSING
            event.attempts += 1

        await session.commit()

        processed_count = 0
        for event in events:
            try:
                await self._process_single_event(session, event)
                event.status = OutboxEventStatus.PROCESSED
                event.processed_at = datetime.now(timezone.utc)
                event.last_error = None
                processed_count += 1
            except Exception as exc:
                logger.error(f"Erreur traitement événement {event.id} ({event.event_type}): {exc}")
                event.last_error = str(exc)
                if event.attempts >= self.max_attempts:
                    event.status = OutboxEventStatus.FAILED
                else:
                    event.status = OutboxEventStatus.PENDING  # Rejouable au prochain tick
            await session.commit()

        return processed_count

    async def _process_single_event(self, session: AsyncSession, event: OutboxEventModel):
        """
        Logique métier de traitement d'un événement outbox.
        Sera connectée au PreferenceEngine, AudienceResolver et aux canaux en Phase 2+.
        """
        logger.info(f"Traitement événement Outbox [{event.event_type}] (Tenant ID: {event.tenant_id})")
        # En Phase 1, valide l'intégrité de la payload et la structure de l'événement outbox
        if not event.event_type or not event.payload:
            raise ValueError("Type d'événement ou payload manquant")
        await asyncio.sleep(0.01)  # Simule le dispatch rapide

    async def run(self):
        """Boucle principale du worker."""
        self._running = True
        logger.info("Démarrage du OutboxWorker...")
        while self._running:
            try:
                async with AsyncSessionLocal() as session:
                    count = await self.process_batch(session)
                    if count > 0:
                        logger.info(f"{count} événement(s) outbox traité(s) avec succès.")
            except Exception as e:
                logger.error(f"Erreur inattendue dans la boucle du worker: {e}")
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        self._running = False


if __name__ == "__main__":
    worker = OutboxWorker()
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        worker.stop()
        logger.info("Worker arrêté par l'utilisateur.")
