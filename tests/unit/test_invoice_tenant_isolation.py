import pytest
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from shared_kernel.infrastructure.database import Base
from monetization_context.infrastructure.persistence.models import InvoiceModel
from monetization_context.application.services.invoice_application_service import InvoiceApplicationService

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.mark.asyncio
async def test_b10_tenant_isolation_invoice_access():
    """Vérifie le rejet (403) si l'admin du Tenant A tente d'accéder à la facture du Tenant B (B10)."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    tenant_a_id = uuid.uuid4()
    tenant_b_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    async with async_session() as session:
        # Créer une facture pour le Tenant B
        inv_b = InvoiceModel(
            id=uuid.uuid4(),
            tenant_id=tenant_b_id,
            number="FAC-2027-TENANTB-0001",
            academic_year="2026-2027",
            status="ISSUED",
            subtotal_xaf=500000,
            tax_rate_percent=0,
            tax_xaf=0,
            total_xaf=500000,
            issue_date=now,
            due_date=now,
        )
        session.add(inv_b)
        await session.commit()
        inv_b_id = inv_b.id

    async with async_session() as session:
        service = InvoiceApplicationService(session)

        # Tenant B peut lire sa propre facture
        inv_fetched = await service.get_invoice_by_id(inv_b_id, requesting_tenant_id=tenant_b_id)
        assert inv_fetched.id == inv_b_id

        # Super Admin peut lire la facture de n'importe quel tenant
        inv_admin = await service.get_invoice_by_id(inv_b_id, requesting_tenant_id=tenant_a_id, is_super_admin=True)
        assert inv_admin.id == inv_b_id

        # Tenant A tente de lire la facture de Tenant B -> 403 Forbidden
        with pytest.raises(HTTPException) as exc_info:
            await service.get_invoice_by_id(inv_b_id, requesting_tenant_id=tenant_a_id, is_super_admin=False)
        
        assert exc_info.value.status_code == 403
        assert "Accès refusé" in exc_info.value.detail

    await engine.dispose()
