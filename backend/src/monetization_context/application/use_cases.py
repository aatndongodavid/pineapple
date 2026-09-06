# backend/src/monetization_context/application/use_cases.py

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from monetization_context.application.dtos import (
    LicenseStatusDTO,
    SponsorshipCreateDTO,
    SponsorshipResponseDTO,
)
from monetization_context.domain.entities import CampusLicense, Sponsorship
from monetization_context.domain.ports import MonetizationRepositoryPort
from monetization_context.domain.value_objects import (
    CampusLicenseTier,
    SponsorshipStatus,
)
from shared_kernel.domain.value_objects import Money


class SponsorshipNotFoundError(Exception):
    pass


class LicenseNotFoundError(Exception):
    pass


class InvalidSponsorshipDatesError(Exception):
    pass


class CreateSponsorshipUseCase:
    """Création d'une campagne sponsorisée multi-établissements."""

    def __init__(self, monetization_repo: MonetizationRepositoryPort):
        self._monetization_repo = monetization_repo

    async def execute(
        self,
        tenant_id: UUID,
        dto: SponsorshipCreateDTO,
    ) -> SponsorshipResponseDTO:
        # Validation basique des dates
        if dto.start_date >= dto.end_date:
            raise InvalidSponsorshipDatesError("start_date must be before end_date")

        # Vérifier que le budget est positif
        if dto.budget_fcfa <= 0:
            raise ValueError("Budget must be positive")

        sponsorship = Sponsorship(
            id=uuid4(),
            tenant_id=tenant_id,
            organization_id=dto.organization_id,
            target_tenant_ids=dto.target_tenant_ids,
            budget=Money(amount=Decimal(dto.budget_fcfa), currency="XAF"),
            status=SponsorshipStatus.PENDING,  # Le statut initial est PENDING
            start_date=dto.start_date,
            end_date=dto.end_date,
            created_at=datetime.utcnow(),
        )

        saved = await self._monetization_repo.save_sponsorship(sponsorship)

        return SponsorshipResponseDTO(
            id=saved.id,
            tenant_id=saved.tenant_id,
            organization_id=saved.organization_id,
            target_tenant_ids=saved.target_tenant_ids,
            budget_fcfa=int(saved.budget.amount),
            status=saved.status,
            start_date=saved.start_date,
            end_date=saved.end_date,
        )


class CheckCampusLicenseUseCase:
    """Vérification de l'état de la licence Campus d'un établissement."""

    def __init__(self, monetization_repo: MonetizationRepositoryPort):
        self._monetization_repo = monetization_repo

    async def execute(self, tenant_id: UUID) -> LicenseStatusDTO:
        license = await self._monetization_repo.get_license_by_tenant(tenant_id)
        if not license:
            raise LicenseNotFoundError("No license found for this tenant")

        return LicenseStatusDTO(
            tenant_id=license.tenant_id,
            tier=license.tier,
            is_active=license.is_active,
            max_certified_students=license.max_certified_students,
            expires_at=license.expires_at,
        )