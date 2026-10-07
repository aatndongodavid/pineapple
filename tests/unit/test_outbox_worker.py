# tests/unit/test_outbox_worker.py

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select, delete

from shared_kernel.domain.events import ClassAnnouncementPublishedEvent
from identity_context.infrastructure.persistence.models import TenantModel
from notification_context.infrastructure.persistence.models import OutboxEventModel
from notification_context.domain.value_objects import OutboxEventStatus
from notification_context.worker import OutboxWorker


@pytest.mark.asyncio
async def test_outbox_event_persistence_and_processing(
    session_factory,
    tenant_id_fixture,
):
    """
    Test Gate M4/M5: Vérification de l'inscription transactionnelle dans outbox_events
    et du dépilage par le worker.
    """
    event = ClassAnnouncementPublishedEvent(
        tenant_id=tenant_id_fixture,
        class_group_id=uuid.uuid4(),
        announcement_id=uuid.uuid4(),
        title="Examen final lundi à 08h00",
        author_id=uuid.uuid4(),
    )

    async with session_factory() as db:
        await db.execute(delete(OutboxEventModel))
        # Seed tenant
        tenant = (await db.execute(select(TenantModel).where(TenantModel.id == tenant_id_fixture))).scalars().first()
        if not tenant:
            tenant = TenantModel(id=tenant_id_fixture, name="École Test Outbox", code=f"OUT_{uuid.uuid4().hex[:4]}", is_active=True)
            db.add(tenant)

        outbox_record = OutboxEventModel(
            id=event.event_id,
            tenant_id=event.tenant_id,
            event_type=event.event_type,
            payload=event.payload,
            status=OutboxEventStatus.PENDING,
        )
        db.add(outbox_record)
        await db.commit()

    # Process via worker
    worker = OutboxWorker(batch_size=10, max_attempts=3)
    async with session_factory() as db:
        processed_count = await worker.process_batch(db)
        assert processed_count == 1

        db_record = await db.get(OutboxEventModel, event.event_id)
        assert db_record.status == OutboxEventStatus.PROCESSED
        assert db_record.processed_at is not None
        assert db_record.attempts == 1


@pytest.mark.asyncio
async def test_gate_m5_worker_crash_resilience_and_retry(
    session_factory,
    tenant_id_fixture,
):
    """
    Gate M5: Résilience du worker après échec/crash.
    Répétition avec backoff puis passage en FAILED (Dead-Letter outbox).
    """
    event_id = uuid.uuid4()
    async with session_factory() as db:
        await db.execute(delete(OutboxEventModel))
        outbox_record = OutboxEventModel(
            id=event_id,
            tenant_id=tenant_id_fixture,
            event_type="FAULTY_EVENT",
            payload={},
            status=OutboxEventStatus.PENDING,
        )
        db.add(outbox_record)
        await db.commit()

    worker = OutboxWorker(batch_size=10, max_attempts=3)

    # Mock _process_single_event to raise an exception
    async def faulty_process(session, ev):
        raise RuntimeError("Simulated network outage to email provider")

    worker._process_single_event = faulty_process

    # Attempt 1 -> should fail and remain PENDING for retry
    async with session_factory() as db:
        await worker.process_batch(db)
        rec = await db.get(OutboxEventModel, event_id)
        assert rec.status == OutboxEventStatus.PENDING
        assert rec.attempts == 1
        assert "Simulated network outage" in rec.last_error

    # Attempt 2
    async with session_factory() as db:
        await worker.process_batch(db)
        rec = await db.get(OutboxEventModel, event_id)
        assert rec.status == OutboxEventStatus.PENDING
        assert rec.attempts == 2

    # Attempt 3 -> max_attempts reached (3), transitions to FAILED
    async with session_factory() as db:
        await worker.process_batch(db)
        rec = await db.get(OutboxEventModel, event_id)
        assert rec.status == OutboxEventStatus.FAILED
        assert rec.attempts == 3
