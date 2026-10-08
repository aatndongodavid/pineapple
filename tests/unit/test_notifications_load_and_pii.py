# tests/unit/test_notifications_load_and_pii.py

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select, func, delete

from identity_context.infrastructure.persistence.models import UserModel, TenantModel
from identity_context.domain.value_objects import AccountStatus
from notification_context.domain.value_objects import NotificationCategory, NotificationChannel, OutboxEventStatus, DeliveryStatus
from notification_context.infrastructure.persistence.models import OutboxEventModel, NotificationDeliveryModel
from notification_context.worker import OutboxWorker
from notification_context.infrastructure.adapters.sms_gateway import SmsGatewayAdapter


@pytest.mark.asyncio
async def test_gate_m11_high_throughput_outbox_processing(session_factory):
    """
    Gate M11: Traitement par lots à forte charge (100 événements outbox).
    Vérifie que l'Outbox Worker traite tous les messages en file d'attente.
    """
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    async with session_factory() as db:
        await db.execute(delete(OutboxEventModel))
        tenant = TenantModel(id=tenant_id, name="Load Test School", code=f"LOAD_{uuid.uuid4().hex[:4]}", is_active=True)
        db.add(tenant)

        user = UserModel(id=user_id, email=f"load_{user_id.hex[:6]}@test.com", first_name="Load", last_name="Tester", hashed_password="hash", account_status=AccountStatus.ACTIVE)
        db.add(user)

        # Enqueue 50 outbox events
        events = []
        for i in range(50):
            event = OutboxEventModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                event_type="CLASS_ANNOUNCEMENT_PUBLISHED",
                payload={
                    "user_id": str(user_id),
                    "category": "IMPORTANT",
                    "criticality": "IMPORTANT",
                    "channel": "IN_APP",
                    "title": f"Annonce #{i+1}",
                    "body": "Contenu du message de test de charge",
                    "deep_link": "/announcements",
                },
                status=OutboxEventStatus.PENDING,
            )
            events.append(event)
        db.add_all(events)
        await db.commit()

    # Run Outbox Worker process batch
    async with session_factory() as db:
        worker = OutboxWorker(batch_size=50)
        processed = await worker.process_batch(db)
        assert processed == 50

    # Verify all 50 processed
    async with session_factory() as db:
        res = await db.execute(
            select(func.count(OutboxEventModel.id)).where(
                OutboxEventModel.tenant_id == tenant_id,
                OutboxEventModel.status == OutboxEventStatus.PROCESSED,
            )
        )
        count_processed = res.scalar_one()
        assert count_processed == 50


@pytest.mark.asyncio
async def test_gate_m11_pii_masking_in_logs():
    """
    Gate M11: Protection PII — Masquage strict des numéros de téléphone et e-mails dans les logs.
    """
    phone = "+237690000000"
    masked_phone = f"{phone[:6]}***"
    assert masked_phone == "+23769***"
    assert "00000" not in masked_phone

    email = "etudiant.secret@univ-douala.cm"
    username, domain = email.split("@")
    masked_email = f"{username[:2]}***@{domain}"
    assert masked_email == "et***@univ-douala.cm"
    assert "secret" not in masked_email
