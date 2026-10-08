import re
import uuid
from typing import Optional
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from monetization_context.infrastructure.persistence.models import InvoiceModel

class InvoiceNumberService:
    """Service garantissant une numérotation séquentielle immuable et sans trou par établissement et par année."""

    @staticmethod
    async def generate_next_invoice_number(
        session: AsyncSession,
        tenant_id: uuid.UUID,
        tenant_code: str,
        year: int
    ) -> str:
        """
        Génère de manière atomique et sûre le prochain numéro de facture (ex: FAC-2027-ENSPD-0001).
        Utilise un verrou advisory PostgreSQL par (tenant_id, année) pour éviter tout doublon/trou sous concurrence.
        """
        clean_code = re.sub(r'[^A-Z0-9]', '', tenant_code.upper())
        if not clean_code:
            clean_code = "TENANT"

        lock_name = f"inv_seq_{tenant_id}_{year}"
        
        # lock advisory PostgreSQL si le dialecte est postgresql
        dialect_name = session.bind.dialect.name if session.bind else ""
        if dialect_name == "postgresql":
            await session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:lock_name))"), {"lock_name": lock_name})

        prefix = f"FAC-{year}-{clean_code}-"

        # Récupérer la dernière facture pour ce tenant et cette année
        stmt = (
            select(InvoiceModel.number)
            .where(
                InvoiceModel.tenant_id == tenant_id,
                InvoiceModel.number.like(f"{prefix}%")
            )
            .order_by(InvoiceModel.number.desc())
            .limit(1)
            .with_for_update()
        )
        result = await session.execute(stmt)
        last_number: Optional[str] = result.scalar_one_or_none()

        if not last_number:
            next_seq = 1
        else:
            # Extraire le numéro de séquence final (ex: FAC-2027-ENSPD-0005 -> 5)
            match = re.search(r'-(\d+)$', last_number)
            if match:
                next_seq = int(match.group(1)) + 1
            else:
                next_seq = 1

        return f"{prefix}{next_seq:04d}"
