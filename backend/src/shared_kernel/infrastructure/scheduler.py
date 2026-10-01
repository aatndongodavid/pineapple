# backend/src/shared_kernel/infrastructure/scheduler.py

import logging
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_context.domain.services import AlumniRetentionService
from identity_context.domain.value_objects import AcademicStatus, AccountStatus
from identity_context.infrastructure.persistence.models import UserModel
from monetization_context.infrastructure.persistence.models import CampusLicenseModel
from shared_kernel.infrastructure.database import AsyncSessionLocal

logger = logging.getLogger("pineapple.scheduler")


async def run_alumni_archival_job():
    """
    Tâche planifiée quotidienne (APScheduler/Background Job) :
    Identifie les comptes ALUMNI dont la fenêtre de rétention selon le palier de licence
    de leur établissement (BASIC: 6m, STANDARD: 12m) est dépassée, et fait basculer leur
    account_status à ARCHIVED.
    Exclut explicitement les établissements au palier ENTERPRISE.
    """
    logger.info("Démarrage de la tâche planifiée d'archivage des comptes Alumni...")
    async with AsyncSessionLocal() as session:
        try:
            # 1. Charger les licences des tenants
            lic_stmt = select(CampusLicenseModel)
            lic_result = await session.execute(lic_stmt)
            licenses = {l.tenant_id: l.tier for l in lic_result.scalars().all()}

            # 2. Charger les utilisateurs Alumni actifs
            users_stmt = select(UserModel).where(
                UserModel.academic_status == AcademicStatus.ALUMNI,
                UserModel.account_status == AccountStatus.ACTIVE,
            )
            user_result = await session.execute(users_stmt)
            alumni_users = user_result.scalars().all()

            archived_count = 0
            for user_model in alumni_users:
                tier = licenses.get(user_model.tenant_id)
                if not tier:
                    continue

                # Conversion entité rapide pour évaluation du domaine
                from identity_context.domain.entities import User
                user_entity = User(
                    id=user_model.id,
                    tenant_id=user_model.tenant_id,
                    email=user_model.email,
                    first_name=user_model.first_name,
                    last_name=user_model.last_name,
                    matricule=user_model.matricule,
                    faculty=user_model.faculty,
                    filiere=user_model.filiere,
                    academic_year=user_model.academic_year,
                    account_status=user_model.account_status,
                    verification_status=user_model.verification_status,
                    academic_status=user_model.academic_status,
                    role=user_model.role,
                    created_at=user_model.created_at,
                )

                if AlumniRetentionService.is_alumni_expired(user_entity, tier):
                    user_model.account_status = AccountStatus.ARCHIVED
                    archived_count += 1

            if archived_count > 0:
                await session.commit()
            logger.info(f"Tâche d'archivage terminée. {archived_count} comptes Alumni archivés.")
            return archived_count
        except Exception as e:
            await session.rollback()
            logger.error(f"Erreur lors de l'archivage automatique des alumni: {e}")
            return 0
