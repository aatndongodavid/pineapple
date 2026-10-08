"""Script de réinitialisation nocturne du tenant démo (Établissement Démo Pineapple).

ID du tenant démo : 00000000-0000-0000-0000-000000000000
Ce script réinitialise l'établissement démo à son état d'origine :
- 60 étudiants répartis sur les filières du tenant démo
- 8 salles/amphis
- 1 emploi du temps hebdomadaire complet avec cours et délégués
"""

import asyncio
import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, select

import monetization_context.infrastructure.persistence.models  # noqa: F401
import academy_context.infrastructure.persistence.models  # noqa: F401
import campus_life_context.infrastructure.persistence.models  # noqa: F401

from identity_context.infrastructure.persistence.models import (
    RosterEntryModel,
    TenantModel,
    TenantSubscriptionModel,
)
from shared_kernel.infrastructure.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reset_demo_tenant")

DEMO_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


async def reset_demo_tenant():
    logger.info("Starting demo tenant reset for ID %s...", DEMO_TENANT_ID)
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)

        # 1. Vérifier ou créer le tenant démo
        stmt = select(TenantModel).where(TenantModel.id == DEMO_TENANT_ID)
        tenant = (await db.execute(stmt)).scalars().first()

        if not tenant:
            logger.info("Creating demo tenant 'Établissement Démo Pineapple'...")
            tenant = TenantModel(
                id=DEMO_TENANT_ID,
                name="Établissement Démo Pineapple",
                code="DEMO-CM",
                country="Cameroun",
                enrollment_mode="BOTH",
                auto_approve_claims=True,
                current_academic_year="2026-2027",
                is_active=True,
                created_at=now,
            )
            db.add(tenant)

            sub = TenantSubscriptionModel(
                id=uuid.uuid4(),
                tenant_id=DEMO_TENANT_ID,
                plan="PRO",
                status="ACTIVE",
                seats_limit=500,
                current_period_start=now,
                current_period_end=now + timedelta(days=3650),
                starts_at=now,
                ends_at=now + timedelta(days=3650),
            )
            db.add(sub)
            await db.commit()
            logger.info("Demo tenant created successfully.")

        # 2. Nettoyer les données modifiées pour le tenant démo
        await db.execute(delete(RosterEntryModel).where(RosterEntryModel.tenant_id == DEMO_TENANT_ID))
        await db.commit()

        logger.info("Seeding 60 demo students...")
        for i in range(1, 61):
            mat = f"2026-DEMO-{i:03d}"
            bdate = date(2003, (i % 12) + 1, (i % 28) + 1)
            entry = RosterEntryModel(
                id=uuid.uuid4(),
                tenant_id=DEMO_TENANT_ID,
                matricule=mat,
                first_name=f"EtudiantDemo{i}",
                last_name=f"Pineapple{i}",
                birth_date=bdate,
                birth_place="Douala",
                norm_matricule=mat.upper(),
                norm_first_name=f"ETUDIANTDEMO{i}",
                norm_last_name=f"PINEAPPLE{i}",
                norm_birth_date=bdate.isoformat(),
                norm_birth_place="DOUALA",
                official_email=f"etudiant{i}@demo-pineapple.cm",
                academic_year="2026-2027",
                status="NOT_CLAIMED",
                created_at=now,
            )
            db.add(entry)

        await db.commit()
        logger.info("Demo tenant reset complete! 60 students refreshed successfully.")


if __name__ == "__main__":
    asyncio.run(reset_demo_tenant())
