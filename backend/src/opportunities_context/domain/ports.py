# backend/src/opportunities_context/domain/ports.py

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from opportunities_context.domain.entities import Opportunity, ProjectApplication
from opportunities_context.domain.value_objects import OpportunityType, OpportunityStatus


class OpportunityRepositoryPort(ABC):
    """Port de persistance pour le contexte Opportunities."""

    @abstractmethod
    async def save_opportunity(self, opportunity: Opportunity) -> Opportunity:
        """Sauvegarde une opportunité (création ou mise à jour)."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, opportunity_id: UUID, tenant_id: UUID) -> Optional[Opportunity]:
        """Récupère une opportunité par son identifiant dans un tenant donné."""
        raise NotImplementedError

    @abstractmethod
    async def list_opportunities(
        self,
        tenant_id: UUID,
        opportunity_type: Optional[OpportunityType] = None,
        status: Optional[OpportunityStatus] = None,
    ) -> List[Opportunity]:
        """Liste les opportunités d'un tenant avec filtres optionnels."""
        raise NotImplementedError

    @abstractmethod
    async def save_application(self, application: ProjectApplication) -> ProjectApplication:
        """Sauvegarde une candidature."""
        raise NotImplementedError

    @abstractmethod
    async def list_applications_for_opportunity(
        self, opportunity_id: UUID
    ) -> List[ProjectApplication]:
        """Liste toutes les candidatures pour une opportunité donnée."""
        raise NotImplementedError