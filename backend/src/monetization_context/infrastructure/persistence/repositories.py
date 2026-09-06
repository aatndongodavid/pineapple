# backend/src/monetization_context/infrastructure/persistence/repositories.py

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from monetization_context.domain.entities import CampusLicense, Sponsorship
from monetization_context.domain.ports import MonetizationRepositoryPort
from monetization_context.domain.value_objects import (
    CampusLicenseTier,
    SponsorshipStatus,
    SubscriptionPlan,
)
from monetization_context.infrastructure.persistence.models import (
    CampusLicenseModel,
    SponsorshipModel,
)
from shared_kernel.domain.value_objects import Money


class PostgresMonetizationRepository(MonetizationRepositoryPort):
    """Implémentation PostgreSQL du port MonetizationRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    # ----- Sponsorship -----
    @staticmethod
    def _sponsorship_to_entity(model: SponsorshipModel) -> Sponsorship:
        return Sponsorship(
            id=model.id,
            tenant_id=model.tenant_id,
            organization_id=model.organization_id,
            target_tenant_ids=[UUID(t) for t in model.target_tenant_ids],
            budget=Money(amount=Decimal(model.budget_amount), currency="XAF"),
            status=model.status,
            start_date=model.start_date,
            end_date=model.end_date,
            created_at=model.created_at,
        )

    @staticmethod
    def _sponsorship_to_model(sponsorship: Sponsorship) -> SponsorshipModel:
        return SponsorshipModel(
            id=sponsorship.id,
            tenant_id=sponsorship.tenant_id,
            organization_id=sponsorship.organization_id,
            target_tenant_ids=[str(t) for t in sponsorship.target_tenant_ids],
            budget_amount=int(sponsorship.budget.amount),
            status=sponsorship.status,
            start_date=sponsorship.start_date,
            end_date=sponsorship.end_date,
            created_at=sponsorship.created_at,
        )

    async def save_sponsorship(self, sponsorship: Sponsorship) -> Sponsorship:
        async with self._session_factory() as session:
            model = self._sponsorship_to_model(sponsorship)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return sponsorship

    async def get_sponsorship_by_id(self, sponsorship_id: UUID, tenant_id: UUID) -> Optional[Sponsorship]:
        async with self._session_factory() as session:
            stmt = select(SponsorshipModel).where(
                SponsorshipModel.id == sponsorship_id,
                SponsorshipModel.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._sponsorship_to_entity(model) if model else None

    async def list_sponsorships_by_tenant(
        self, tenant_id: UUID, status: Optional[SponsorshipStatus] = None
    ) -> List[Sponsorship]:
        async with self._session_factory() as session:
            stmt = select(SponsorshipModel).where(SponsorshipModel.tenant_id == tenant_id)
            if status is not None:
                stmt = stmt.where(SponsorshipModel.status == status)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._sponsorship_to_entity(m) for m in models]

    # ----- CampusLicense -----
    @staticmethod
    def _license_to_entity(model: CampusLicenseModel) -> CampusLicense:
        return CampusLicense(
            id=model.id,
            tenant_id=model.tenant_id,
            tier=model.tier,
            max_certified_students=model.max_certified_students,
            is_active=model.is_active,
            expires_at=model.expires_at,
            created_at=model.created_at,
        )

    @staticmethod
    def _license_to_model(license: CampusLicense) -> CampusLicenseModel:
        return CampusLicenseModel(
            id=license.id,
            tenant_id=license.tenant_id,
            tier=license.tier,
            max_certified_students=license.max_certified_students,
            is_active=license.is_active,
            expires_at=license.expires_at,
            created_at=license.created_at,
        )

    async def save_license(self, license: CampusLicense) -> CampusLicense:
        async with self._session_factory() as session:
            model = self._license_to_model(license)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return license

    async def get_license_by_tenant(self, tenant_id: UUID) -> Optional[CampusLicense]:
        async with self._session_factory() as session:
            stmt = select(CampusLicenseModel).where(CampusLicenseModel.tenant_id == tenant_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._license_to_entity(model) if model else None

    async def list_licenses_by_tier(self, tier: Optional[CampusLicenseTier] = None) -> List[CampusLicense]:
        async with self._session_factory() as session:
            stmt = select(CampusLicenseModel)
            if tier is not None:
                stmt = stmt.where(CampusLicenseModel.tier == tier)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._license_to_entity(m) for m in models]

    # ----- Club Subscription (simplified) -----
    async def save_club_subscription(
        self,
        tenant_id: UUID,
        organization_id: UUID,
        plan: SubscriptionPlan,
        start_date: datetime,
        end_date: datetime,
        is_active: bool = True,
    ) -> None:
        # Implémentation minimale : à compléter selon les besoins (table spécifique)
        # Pour l'instant, on lève une exception ou on ne fait rien.
        # Le port l'exige, mais on peut laisser une implémentation factice.
        pass