# backend/src/opportunities_context/application/use_cases.py

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from opportunities_context.application.dtos import (
    ApplicationCreateDTO,
    OpportunityCreateDTO,
)
from opportunities_context.domain.entities import Opportunity, ProjectApplication
from opportunities_context.domain.ports import OpportunityRepositoryPort
from opportunities_context.domain.value_objects import (
    ApplicationStatus,
    OpportunityStatus,
    OpportunityType,
)


class OpportunityNotFoundError(Exception):
    pass


class ApplicationAlreadyExistsError(Exception):
    pass


class CreateOpportunityUseCase:
    """Création d'une opportunité (projet, recherche, stage, etc.)."""

    def __init__(self, opportunity_repo: OpportunityRepositoryPort):
        self._opportunity_repo = opportunity_repo

    async def execute(
        self,
        creator_id: UUID,
        tenant_id: UUID,
        dto: OpportunityCreateDTO,
    ) -> Opportunity:
        opportunity = Opportunity(
            id=uuid4(),
            tenant_id=tenant_id,
            creator_id=creator_id,
            title=dto.title,
            description=dto.description,
            type=dto.type,
            required_skills=dto.required_skills,
            status=dto.status,
            max_applicants=dto.max_applicants,
            created_at=datetime.utcnow(),
        )
        return await self._opportunity_repo.save_opportunity(opportunity)


class ApplyToOpportunityUseCase:
    """Soumission d'une candidature à une opportunité."""

    def __init__(self, opportunity_repo: OpportunityRepositoryPort):
        self._opportunity_repo = opportunity_repo

    async def execute(
        self,
        applicant_user_id: UUID,
        tenant_id: UUID,
        dto: ApplicationCreateDTO,
    ) -> ProjectApplication:
        opportunity = await self._opportunity_repo.get_by_id(dto.opportunity_id, tenant_id)
        if not opportunity:
            raise OpportunityNotFoundError("Opportunité introuvable.")

        if opportunity.status != OpportunityStatus.OPEN:
            raise ValueError("Cette opportunité n'est pas ouverte aux candidatures.")

        # Vérifier que l'utilisateur n'a pas déjà postulé (à implémenter si nécessaire)
        # Ici on suppose que le repository ne le gère pas ; on peut ajouter une méthode dédiée.

        application = ProjectApplication(
            id=uuid4(),
            opportunity_id=dto.opportunity_id,
            applicant_user_id=applicant_user_id,
            cover_letter=dto.cover_letter,
            status=ApplicationStatus.PENDING,
            applied_at=datetime.utcnow(),
        )
        return await self._opportunity_repo.save_application(application)


class ListOpportunitiesUseCase:
    """Liste des opportunités avec filtres."""

    def __init__(self, opportunity_repo: OpportunityRepositoryPort):
        self._opportunity_repo = opportunity_repo

    async def execute(
        self,
        tenant_id: UUID,
        opportunity_type: Optional[OpportunityType] = None,
        status: Optional[OpportunityStatus] = None,
    ) -> List[Opportunity]:
        return await self._opportunity_repo.list_opportunities(
            tenant_id=tenant_id,
            opportunity_type=opportunity_type,
            status=status,
        )