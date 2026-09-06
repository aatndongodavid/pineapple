# backend/src/api/v1/monetization_router.py

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from monetization_context.application.dtos import (
    LicenseStatusDTO,
    SponsorshipCreateDTO,
    SponsorshipResponseDTO,
)
from monetization_context.application.use_cases import (
    CheckCampusLicenseUseCase,
    CreateSponsorshipUseCase,
    InvalidSponsorshipDatesError,
    LicenseNotFoundError,
)
from monetization_context.infrastructure.persistence.repositories import (
    PostgresMonetizationRepository,
)
from shared_kernel.config import settings
from shared_kernel.infrastructure.database import AsyncSessionLocal
from shared_kernel.infrastructure.tenant_middleware import get_current_tenant_id

security = HTTPBearer()


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return AsyncSessionLocal


async def get_monetization_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresMonetizationRepository:
    return PostgresMonetizationRepository(session_factory)


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


router = APIRouter(prefix="/monetization", tags=["Monetization & Licenses"])


@router.post("/sponsoring", response_model=SponsorshipResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_sponsorship(
    dto: SponsorshipCreateDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    monetization_repo: PostgresMonetizationRepository = Depends(get_monetization_repo),
):
    """
    Créer une campagne sponsorisée multi-établissements.
    """
    use_case = CreateSponsorshipUseCase(monetization_repo)
    try:
        result = await use_case.execute(tenant_id=tenant_id, dto=dto)
    except InvalidSponsorshipDatesError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@router.get("/license/status", response_model=LicenseStatusDTO)
async def get_license_status(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    monetization_repo: PostgresMonetizationRepository = Depends(get_monetization_repo),
):
    """
    Vérifier l'état de la licence Campus de l'établissement.
    """
    use_case = CheckCampusLicenseUseCase(monetization_repo)
    try:
        status_dto = await use_case.execute(tenant_id=tenant_id)
    except LicenseNotFoundError:
        raise HTTPException(status_code=404, detail="No license found for this tenant")

    return status_dto