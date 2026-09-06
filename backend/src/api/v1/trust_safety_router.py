# backend/src/api/v1/trust_safety_router.py

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from trust_safety_context.application.dtos import (
    ReportResponseDTO,
    ReviewReportDTO,
    ReviewReportResponseDTO,
    SubmitReportDTO,
)
from trust_safety_context.application.use_cases import (
    InvalidReviewError,
    ReportNotFoundError,
    ReviewReportUseCase,
    SubmitReportUseCase,
)
from trust_safety_context.infrastructure.persistence.repositories import (
    PostgresTrustSafetyRepository,
)
from shared_kernel.config import settings
from shared_kernel.infrastructure.database import AsyncSessionLocal
from shared_kernel.infrastructure.tenant_middleware import get_current_tenant_id

security = HTTPBearer()


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return AsyncSessionLocal


async def get_trust_safety_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresTrustSafetyRepository:
    return PostgresTrustSafetyRepository(session_factory)


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


async def get_moderator_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    # TODO: Vérifier le rôle modérateur/admin à partir du JWT ou d'un service RBAC.
    # Pour l'instant, on accepte tout utilisateur authentifié en tant que modérateur.
    # Dans une vraie implémentation, on lèverait une 403 si l'utilisateur n'a pas le rôle.
    return current_user


router = APIRouter(prefix="/trust-safety", tags=["Trust & Safety"])


@router.post("/report", response_model=ReportResponseDTO, status_code=status.HTTP_201_CREATED)
async def submit_report(
    dto: SubmitReportDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    repo: PostgresTrustSafetyRepository = Depends(get_trust_safety_repo),
):
    """
    Soumettre un signalement de contenu ou de comportement.
    """
    use_case = SubmitReportUseCase(repo)
    report = await use_case.execute(
        reporter_user_id=current_user["user_id"],
        tenant_id=tenant_id,
        dto=dto,
    )
    return ReportResponseDTO(
        id=report.id,
        tenant_id=report.tenant_id,
        reporter_user_id=report.reporter_user_id,
        target_type=report.target_type,
        target_id=report.target_id,
        reason=report.reason,
        status=report.status,
        created_at=report.created_at,
    )


@router.post("/moderation/review", response_model=ReviewReportResponseDTO)
async def review_report(
    dto: ReviewReportDTO,
    moderator: dict = Depends(get_moderator_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    repo: PostgresTrustSafetyRepository = Depends(get_trust_safety_repo),
):
    """
    Examiner un signalement (réservé aux modérateurs).
    """
    use_case = ReviewReportUseCase(repo)
    try:
        result = await use_case.execute(
            moderator_user_id=moderator["user_id"],
            tenant_id=tenant_id,
            dto=dto,
        )
    except ReportNotFoundError:
        raise HTTPException(status_code=404, detail="Report not found")
    except InvalidReviewError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result