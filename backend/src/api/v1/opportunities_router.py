# backend/src/api/v1/opportunities_router.py

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from opportunities_context.application.dtos import (
    ApplicationCreateDTO,
    ApplicationResponseDTO,
    OpportunityCreateDTO,
    OpportunityResponseDTO,
)
from opportunities_context.application.use_cases import (
    ApplyToOpportunityUseCase,
    CreateOpportunityUseCase,
    ListOpportunitiesUseCase,
    OpportunityNotFoundError,
)
from opportunities_context.domain.value_objects import OpportunityStatus, OpportunityType
from opportunities_context.infrastructure.persistence.repositories import (
    PostgresOpportunityRepository,
)
from shared_kernel.config import settings
from shared_kernel.infrastructure.database import AsyncSessionLocal
from shared_kernel.infrastructure.tenant_middleware import get_current_tenant_id

security = HTTPBearer()


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return AsyncSessionLocal


async def get_opportunity_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresOpportunityRepository:
    return PostgresOpportunityRepository(session_factory)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = uuid.UUID(payload.get("sub"))
        token_tenant = uuid.UUID(payload.get("tenant_id"))
        if token_tenant != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tenant mismatch",
            )
        return {"user_id": user_id, "tenant_id": tenant_id}
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


router = APIRouter(prefix="/opportunities", tags=["Opportunities & Research"])


@router.get("/", response_model=List[OpportunityResponseDTO])
async def list_opportunities(
    opportunity_type: Optional[OpportunityType] = Query(None),
    status_filter: Optional[OpportunityStatus] = Query(None, alias="status"),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    opportunity_repo: PostgresOpportunityRepository = Depends(get_opportunity_repo),
):
    """
    Lister les projets, stages et offres de recherche.
    """
    use_case = ListOpportunitiesUseCase(opportunity_repo)
    opportunities = await use_case.execute(
        tenant_id=tenant_id,
        opportunity_type=opportunity_type,
        status=status_filter,
    )
    return [
        OpportunityResponseDTO(
            id=o.id,
            tenant_id=o.tenant_id,
            creator_id=o.creator_id,
            title=o.title,
            description=o.description,
            type=o.type,
            required_skills=o.required_skills,
            status=o.status,
            max_applicants=o.max_applicants,
            created_at=o.created_at,
        )
        for o in opportunities
    ]


@router.post("/", response_model=OpportunityResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    dto: OpportunityCreateDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    opportunity_repo: PostgresOpportunityRepository = Depends(get_opportunity_repo),
):
    """
    Créer une opportunité (projet, recherche, stage, etc.).
    """
    use_case = CreateOpportunityUseCase(opportunity_repo)
    opportunity = await use_case.execute(
        creator_id=current_user["user_id"],
        tenant_id=tenant_id,
        dto=dto,
    )
    return OpportunityResponseDTO(
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


@router.post("/{opportunity_id}/apply", response_model=ApplicationResponseDTO, status_code=status.HTTP_201_CREATED)
async def apply_to_opportunity(
    opportunity_id: uuid.UUID,
    dto: ApplicationCreateDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    opportunity_repo: PostgresOpportunityRepository = Depends(get_opportunity_repo),
):
    """
    Postuler à une opportunité.
    """
    # S'assurer que l'ID dans le chemin correspond à celui du DTO
    if dto.opportunity_id != opportunity_id:
        raise HTTPException(status_code=400, detail="Opportunity ID mismatch")

    use_case = ApplyToOpportunityUseCase(opportunity_repo)
    try:
        application = await use_case.execute(
            applicant_user_id=current_user["user_id"],
            tenant_id=tenant_id,
            dto=dto,
        )
    except OpportunityNotFoundError:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApplicationResponseDTO(
        id=application.id,
        opportunity_id=application.opportunity_id,
        applicant_user_id=application.applicant_user_id,
        cover_letter=application.cover_letter,
        status=application.status,
        applied_at=application.applied_at,
    )