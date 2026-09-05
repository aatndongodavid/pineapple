# backend/src/monetization_context/domain/ports.py

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from monetization_context.domain.entities import CampusLicense, Sponsorship
from monetization_context.domain.value_objects import (
    CampusLicenseTier,
    SponsorshipStatus,
    SubscriptionPlan,
)


class MonetizationRepositoryPort(ABC):
    """Port de persistance pour le contexte de monétisation."""

    @abstractmethod
    async def save_sponsorship(self, sponsorship: Sponsorship) -> Sponsorship:
        """Sauvegarde un contrat de sponsoring."""
        raise NotImplementedError

    @abstractmethod
    async def get_sponsorship_by_id(
        self, sponsorship_id: UUID, tenant_id: UUID
    ) -> Optional[Sponsorship]:
        """Récupère un sponsoring par son identifiant et tenant."""
        raise NotImplementedError

    @abstractmethod
    async def list_sponsorships_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[SponsorshipStatus] = None,
    ) -> List[Sponsorship]:
        """Liste les sponsoring d'un tenant avec filtre optionnel de statut."""
        raise NotImplementedError

    @abstractmethod
    async def save_license(self, license: CampusLicense) -> CampusLicense:
        """Sauvegarde une licence d'établissement."""
        raise NotImplementedError

    @abstractmethod
    async def get_license_by_tenant(self, tenant_id: UUID) -> Optional[CampusLicense]:
        """Récupère la licence active d'un tenant."""
        raise NotImplementedError

    @abstractmethod
    async def list_licenses_by_tier(
        self, tier: Optional[CampusLicenseTier] = None
    ) -> List[CampusLicense]:
        """Liste les licences selon un tier optionnel."""
        raise NotImplementedError

    @abstractmethod
    async def save_club_subscription(
        self,
        tenant_id: UUID,
        organization_id: UUID,
        plan: SubscriptionPlan,
        start_date: datetime,
        end_date: datetime,
        is_active: bool = True,
    ) -> None:
        """Enregistre ou met à jour l'abonnement d'un club."""
        raise NotImplementedError