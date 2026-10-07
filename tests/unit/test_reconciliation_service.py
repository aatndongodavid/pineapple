# tests/unit/test_reconciliation_service.py

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from monetization_context.infrastructure.persistence.models import (
    Base,
    InvoiceModel,
    PaymentAttemptModel,
    PaymentModel,
)
from monetization_context.infrastructure.adapters.fake_payment_provider import FakePaymentProviderAdapter
from monetization_context.application.services.reconciliation_service import ReconciliationService
from monetization_context.domain.value_objects import PaymentStatus, InvoiceStatus


@pytest.fixture
async def async_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_reconciliation_resolves_pending_payment_to_succeeded(async_session: AsyncSession):
    """Vérifie que la réconciliation passe les paiements PENDING à SUCCEEDED si l'agrégateur confirme."""
    tenant_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # 1. Créer une facture UNPAID et une tentative PENDING
    invoice = InvoiceModel(
        id=invoice_id,
        tenant_id=tenant_id,
        number="FAC-2027-TEST-0001",
        academic_year="2026-2027",
        status=InvoiceStatus.ISSUED,
        subtotal_xaf=500000,
        tax_rate_percent=0,
        tax_xaf=0,
        total_xaf=500000,
        issue_date=now,
        due_date=now,
    )
    attempt = PaymentAttemptModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        amount_xaf=500000,
        channel="MOBILE_MONEY",
        provider_name="CAMPAY",
        provider_ref="CAMPAY-REF-100",
        status=PaymentStatus.PENDING,
    )
    async_session.add(invoice)
    async_session.add(attempt)
    await async_session.commit()

    # 2. Mock du provider avec statut SUCCEEDED
    provider = FakePaymentProviderAdapter()
    provider.transactions["CAMPAY-REF-100"] = {
        "provider_ref": "CAMPAY-REF-100",
        "status": PaymentStatus.SUCCEEDED,
        "amount_xaf": 500000,
    }

    # 3. Exécuter la réconciliation
    rec_service = ReconciliationService(session=async_session, payment_provider=provider)
    anomalies = await rec_service.reconcile_pending_attempts()

    assert len(anomalies) == 0

    # 4. Vérifier que la tentative et la facture sont à jour
    await async_session.refresh(attempt)
    await async_session.refresh(invoice)

    assert attempt.status == PaymentStatus.SUCCEEDED
    assert invoice.status == InvoiceStatus.PAID


@pytest.mark.asyncio
async def test_reconciliation_flags_amount_mismatch_anomaly(async_session: AsyncSession):
    """Vérifie qu'un montant différent retourné par l'agrégateur génère une anomalie AMOUNT_MISMATCH."""
    tenant_id = uuid.uuid4()
    invoice_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    invoice = InvoiceModel(
        id=invoice_id,
        tenant_id=tenant_id,
        number="FAC-2027-TEST-0002",
        academic_year="2026-2027",
        status=InvoiceStatus.ISSUED,
        subtotal_xaf=500000,
        tax_rate_percent=0,
        tax_xaf=0,
        total_xaf=500000,
        issue_date=now,
        due_date=now,
    )
    attempt = PaymentAttemptModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        amount_xaf=500000,
        channel="MOBILE_MONEY",
        provider_name="CAMPAY",
        provider_ref="CAMPAY-REF-200",
        status=PaymentStatus.PENDING,
    )
    async_session.add(invoice)
    async_session.add(attempt)
    await async_session.commit()

    # Provider qui retourne un montant différent (e.g. 400 000 XAF au lieu de 500 000 XAF)
    provider = FakePaymentProviderAdapter()
    provider.transactions["CAMPAY-REF-200"] = {
        "provider_ref": "CAMPAY-REF-200",
        "status": PaymentStatus.SUCCEEDED,
        "amount_xaf": 400000,
    }

    rec_service = ReconciliationService(session=async_session, payment_provider=provider)
    anomalies = await rec_service.reconcile_pending_attempts()

    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == "AMOUNT_MISMATCH"
    assert anomalies[0].db_amount_xaf == 500000
    assert anomalies[0].provider_amount_xaf == 400000


@pytest.mark.asyncio
async def test_reconciliation_flags_status_mismatch_anomaly(async_session: AsyncSession):
    """Vérifie que scan_all_anomalies détecte une tentative marquée SUCCEEDED en DB mais FAILED chez le provider."""
    tenant_id = uuid.uuid4()
    invoice_id = uuid.uuid4()

    attempt = PaymentAttemptModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        amount_xaf=500000,
        channel="MOBILE_MONEY",
        provider_name="CAMPAY",
        provider_ref="CAMPAY-REF-300",
        status=PaymentStatus.SUCCEEDED,
    )
    async_session.add(attempt)
    await async_session.commit()

    provider = FakePaymentProviderAdapter()
    provider.transactions["CAMPAY-REF-300"] = {
        "provider_ref": "CAMPAY-REF-300",
        "status": PaymentStatus.FAILED,
        "amount_xaf": 500000,
    }
    rec_service = ReconciliationService(session=async_session, payment_provider=provider)
    anomalies = await rec_service.scan_all_anomalies()

    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == "STATUS_MISMATCH"
    assert anomalies[0].db_status == PaymentStatus.SUCCEEDED
    assert anomalies[0].provider_status == PaymentStatus.FAILED
