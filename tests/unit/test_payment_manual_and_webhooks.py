import pytest
import uuid
import json
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.pool import StaticPool

from shared_kernel.infrastructure.database import Base
from monetization_context.domain.value_objects import (
    InvoiceStatus,
    PaymentStatus,
    ManualProofStatus,
    SubscriptionStatus,
)
from monetization_context.infrastructure.persistence.models import (
    InvoiceModel,
    PaymentModel,
    PaymentAttemptModel,
    PaymentEventModel,
    ManualPaymentProofModel,
)
from identity_context.infrastructure.persistence.models import TenantSubscriptionModel
from monetization_context.infrastructure.adapters.fake_payment_provider import FakePaymentProviderAdapter
from monetization_context.application.services.payment_application_service import PaymentApplicationService

import pytest_asyncio

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def session_factory(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.mark.asyncio
async def test_b6_manual_payment_proof_workflow(session_factory):
    """B6: Preuve de virement/espèces : soumise -> approuvée par super-admin -> facture payée."""
    tenant_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    admin_user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    async with session_factory() as session:
        # 1. Créer une facture en attente pour le tenant
        inv = InvoiceModel(
            id=invoice_id,
            tenant_id=tenant_id,
            number="FAC-2027-ENSPD-0001",
            academic_year="2026-2027",
            status=InvoiceStatus.ISSUED,
            subtotal_xaf=500000,
            tax_rate_percent=0,
            tax_xaf=0,
            total_xaf=500000,
            issue_date=now,
            due_date=now + timedelta(days=30),
        )
        session.add(inv)

        sub = TenantSubscriptionModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            plan="STANDARD",
            status=SubscriptionStatus.TRIAL,
            current_period_start=now,
            current_period_end=now + timedelta(days=14),
            starts_at=now,
            ends_at=now + timedelta(days=14),
        )
        session.add(sub)
        await session.commit()

    async with session_factory() as session:
        service = PaymentApplicationService(session)

        # 2. L'admin téléverse la preuve de paiement manuel
        proof_dto = await service.submit_manual_proof(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            file_path="/uploads/proofs/recette_virement_123.pdf",
            amount_declared_xaf=500000,
            payment_reference="VIR-2027-9988",
        )
        assert proof_dto.status == ManualProofStatus.SUBMITTED

    async with session_factory() as session:
        service = PaymentApplicationService(session)

        # 3. Le super-admin approuve la preuve
        approved_dto = await service.review_manual_proof(
            proof_id=proof_dto.id,
            reviewer_user_id=admin_user_id,
            approve=True,
        )
        assert approved_dto.status == ManualProofStatus.APPROVED

    # 4. Vérifier que la facture est marquée PAID et que l'abonnement est ACTIVE
    async with session_factory() as session:
        inv_res = await session.execute(select(InvoiceModel).where(InvoiceModel.id == invoice_id))
        inv_db = inv_res.scalar_one()
        assert inv_db.status == InvoiceStatus.PAID
        assert inv_db.paid_at is not None

        sub_res = await session.execute(select(TenantSubscriptionModel).where(TenantSubscriptionModel.tenant_id == tenant_id))
        sub_db = sub_res.scalar_one()
        assert sub_db.status == SubscriptionStatus.ACTIVE


@pytest.mark.asyncio
async def test_b1_and_b2_idempotent_webhook_processing(session_factory):
    """B1 & B2: Webhook Mobile Money -> Essai -> paiement -> actif. Même webhook reçu 3 fois -> 1 seul paiement & prolongation."""
    tenant_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    secret = "my_secret_key"
    provider = FakePaymentProviderAdapter(webhook_secret=secret)

    async with session_factory() as session:
        inv = InvoiceModel(
            id=invoice_id,
            tenant_id=tenant_id,
            number="FAC-2027-ENSPD-0002",
            academic_year="2026-2027",
            status=InvoiceStatus.ISSUED,
            subtotal_xaf=300000,
            tax_rate_percent=0,
            tax_xaf=0,
            total_xaf=300000,
            issue_date=now,
            due_date=now + timedelta(days=30),
        )
        session.add(inv)

        sub = TenantSubscriptionModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            plan="STANDARD",
            status=SubscriptionStatus.TRIAL,
            current_period_start=now,
            current_period_end=now + timedelta(days=14),
            starts_at=now,
            ends_at=now + timedelta(days=14),
        )
        session.add(sub)

        attempt = PaymentAttemptModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            amount_xaf=300000,
            channel="MOBILE_MONEY",
            provider_name="CAMPAY",
            provider_ref="REF-CAMPAY-100",
            status=PaymentStatus.PENDING,
        )
        session.add(attempt)
        await session.commit()

        initial_period_end = sub.current_period_end

    # Préparer le webhook simulé
    webhook_payload = {
        "event_id": "evt_campay_9999",
        "reference": "REF-CAMPAY-100",
        "status": "SUCCESS",
        "amount": 300000,
    }
    payload_bytes = json.dumps(webhook_payload).encode("utf-8")
    sig_header = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    # Recevoir le MÊME webhook 3 fois d'affilée (B2 test)
    for i in range(3):
        async with session_factory() as session:
            service = PaymentApplicationService(session, payment_provider=provider)
            res = await service.process_webhook_payload(
                provider_name="CAMPAY",
                payload_bytes=payload_bytes,
                signature_header=sig_header,
                secret=secret,
            )
            if i == 0:
                assert res["status"] == "success"
            else:
                assert res["status"] == "already_processed"

    # Vérifications post-webhook
    async with session_factory() as session:
        # Facture doit être payée
        inv_db = (await session.execute(select(InvoiceModel).where(InvoiceModel.id == invoice_id))).scalar_one()
        assert inv_db.status == InvoiceStatus.PAID

        # Exactement 1 seul paiement enregistré
        pmts = (await session.execute(select(PaymentModel).where(PaymentModel.invoice_id == invoice_id))).scalars().all()
        assert len(pmts) == 1

        # Abonnement passé de TRIAL à ACTIVE et prolongé d'exactement 365 jours
        sub_db = (await session.execute(select(TenantSubscriptionModel).where(TenantSubscriptionModel.tenant_id == tenant_id))).scalar_one()
        assert sub_db.status == SubscriptionStatus.ACTIVE
        sub_end = sub_db.current_period_end
        if sub_end.tzinfo is None:
            sub_end = sub_end.replace(tzinfo=timezone.utc)
        assert sub_end == initial_period_end + timedelta(days=365)


@pytest.mark.asyncio
async def test_b3_invalid_webhook_signature_rejection(session_factory):
    """B3: Webhook avec mauvaise signature -> rejeté, aucun effet sur l'abonnement."""
    provider = FakePaymentProviderAdapter(webhook_secret="correct_secret")
    payload_bytes = json.dumps({"event_id": "evt_bad_sig"}).encode("utf-8")
    bad_signature = "invalid_signature_hash"

    async with session_factory() as session:
        service = PaymentApplicationService(session, payment_provider=provider)
        with pytest.raises(HTTPException) as exc_info:
            await service.process_webhook_payload(
                provider_name="CAMPAY",
                payload_bytes=payload_bytes,
                signature_header=bad_signature,
                secret="correct_secret",
            )
        assert exc_info.value.status_code == 400
        assert "invalide" in exc_info.value.detail.lower() or "rejetée" in exc_info.value.detail.lower()

    # Vérifier qu'un événement de paiement non valide a été consigné pour audit
    async with session_factory() as session:
        events = (await session.execute(select(PaymentEventModel))).scalars().all()
        assert len(events) == 1
        assert events[0].is_signature_valid is False
