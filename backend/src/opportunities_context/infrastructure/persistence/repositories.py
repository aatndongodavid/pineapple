# backend/src/opportunities_context/infrastructure/persistence/repositories.py

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from opportunities_context.domain.entities import Opportunity, ProjectApplication
from opportunities_context.domain.ports import OpportunityRepositoryPort
from opportunities_context.domain.value_objects import (
    ApplicationStatus,
    OpportunityStatus,
    OpportunityType,
)
from opportunities_context.infrastructure.persistence.models import (
    OpportunityModel,
    ProjectApplicationModel,
)


class PostgresOpportunityRepository(OpportunityRepositoryPort):
    """Implémentation PostgreSQL du port OpportunityRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _opportunity_to_entity(model: OpportunityModel) -> Opportunity:
        return Opportunity(
            id=model.id,
            tenant_id=model.tenant_id,
            creator_id=model.creator_id,
            title=model.title,
            description=model.description,
            type=model.type,
            required_skills=model.required_skills,
            status=model.status,
            max_applicants=model.max_applicants,
            created_at=model.created_at,
        )

    @staticmethod
    def _opportunity_to_model(opportunity: Opportunity) -> OpportunityModel:
        return OpportunityModel(
            id=opportunity.id,
            tenant_id=opportunity.tenant_id,
            creator_id=opportunity.creator_id,
            title=opportunity.title,
            description=opportunity.description,
            type=opportunity.type,
            required_skills=opportunity.required_skills,
            status=opportunity.status,
            max_applicants=opportunity.max_applicants,
            created_at=opportunity.created_at,
        )

    @staticmethod
    def _application_to_entity(model: ProjectApplicationModel) -> ProjectApplication:
        return ProjectApplication(
            id=model.id,
            opportunity_id=model.opportunity_id,
            applicant_user_id=model.applicant_user_id,
            cover_letter=model.cover_letter,
            status=model.status,
            applied_at=model.applied_at,
        )

    @staticmethod
    def _application_to_model(application: ProjectApplication) -> ProjectApplicationModel:
        return ProjectApplicationModel(
            id=application.id,
            opportunity_id=application.opportunity_id,
            applicant_user_id=application.applicant_user_id,
            cover_letter=application.cover_letter,
            status=application.status,
            applied_at=application.applied_at,
        )

    async def save_opportunity(self, opportunity: Opportunity) -> Opportunity:
        async with self._session_factory() as session:
            model = self._opportunity_to_model(opportunity)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return opportunity

    async def get_by_id(self, opportunity_id: UUID, tenant_id: UUID) -> Optional[Opportunity]:
        async with self._session_factory() as session:
            stmt = select(OpportunityModel).where(
                OpportunityModel.id == opportunity_id,
                OpportunityModel.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._opportunity_to_entity(model) if model else None

    async def list_opportunities(
        self,
        tenant_id: UUID,
        opportunity_type: Optional[OpportunityType] = None,
        status: Optional[OpportunityStatus] = None,
    ) -> List[Opportunity]:
        async with self._session_factory() as session:
            stmt = select(OpportunityModel).where(OpportunityModel.tenant_id == tenant_id)
            if opportunity_type is not None:
                stmt = stmt.where(OpportunityModel.type == opportunity_type)
            if status is not None:
                stmt = stmt.where(OpportunityModel.status == status)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._opportunity_to_entity(m) for m in models]

    async def save_application(self, application: ProjectApplication) -> ProjectApplication:
        async with self._session_factory() as session:
            model = self._application_to_model(application)
            try:
                session.add(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return application

    async def list_applications_for_opportunity(
        self, opportunity_id: UUID
    ) -> List[ProjectApplication]:
        async with self._session_factory() as session:
            stmt = select(ProjectApplicationModel).where(
                ProjectApplicationModel.opportunity_id == opportunity_id
            )
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._application_to_entity(m) for m in models]