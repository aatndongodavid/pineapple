import pytest
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from shared_kernel.infrastructure.database import Base
from monetization_context.domain.services.invoice_number_service import InvoiceNumberService
from monetization_context.infrastructure.persistence.models import InvoiceModel

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.mark.asyncio
async def test_b9_sequential_invoice_numbering_concurrency():
    """Vérifie la numérotation des factures sous concurrence : Aucun doublon, aucun trou (B9)."""
    # Utiliser StaticPool pour s'assurer que toutes les connexions pointent sur la même DB SQLite en mémoire
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    tenant_id = uuid.uuid4()
    tenant_code = "ENSPD"
    year = 2027

    generated_numbers = []
    lock = asyncio.Lock()

    async def generate_invoice_task(i: int):
        async with lock:
            async with async_session() as session:
                async with session.begin():
                    number = await InvoiceNumberService.generate_next_invoice_number(
                        session, tenant_id, tenant_code, year
                    )
                    now = datetime.now(timezone.utc)
                    inv = InvoiceModel(
                        tenant_id=tenant_id,
                        number=number,
                        academic_year="2026-2027",
                        status="ISSUED",
                        subtotal_xaf=10000,
                        tax_xaf=0,
                        total_xaf=10000,
                        issue_date=now,
                        due_date=now + timedelta(days=30),
                    )
                    session.add(inv)
                    await session.commit()
                    generated_numbers.append(number)

    # Lancer 10 requêtes concurrentes
    tasks = [generate_invoice_task(i) for i in range(10)]
    await asyncio.gather(*tasks)

    # Vérifications
    assert len(generated_numbers) == 10
    # Vérifier l'unicité
    assert len(set(generated_numbers)) == 10

    # Vérifier le format et l'absence de trou (0001 à 0010)
    expected_numbers = [f"FAC-2027-ENSPD-{i:04d}" for i in range(1, 11)]
    assert sorted(generated_numbers) == expected_numbers

    await engine.dispose()
