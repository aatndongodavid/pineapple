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


# --- FACTURES & PDF (PHASE 2) ---

from fastapi.responses import Response
from monetization_context.application.dtos import InvoiceDTO
from monetization_context.application.services.invoice_application_service import InvoiceApplicationService


@router.get("/invoices", response_model=List[InvoiceDTO])
async def list_invoices(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """Lister les factures de l'établissement avec filtre optionnel par statut."""
    async with session_factory() as session:
        service = InvoiceApplicationService(session)
        is_super_admin = current_user.get("user_type") == "PLATFORM_ADMIN"
        return await service.get_tenant_invoices(tenant_id=tenant_id, status_filter=status_filter)


@router.get("/invoices/{invoice_id}", response_model=InvoiceDTO)
async def get_invoice_detail(
    invoice_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """Détail d'une facture avec vérification stricte de l'isolation inter-tenant."""
    async with session_factory() as session:
        service = InvoiceApplicationService(session)
        is_super_admin = current_user.get("user_type") == "PLATFORM_ADMIN"
        invoice_model = await service.get_invoice_by_id(
            invoice_id=invoice_id, requesting_tenant_id=tenant_id, is_super_admin=is_super_admin
        )
        return service._map_to_dto(invoice_model)


@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """Télécharger le PDF officiel de la facture (WeasyPrint / XAF)."""
    async with session_factory() as session:
        service = InvoiceApplicationService(session)
        is_super_admin = current_user.get("user_type") == "PLATFORM_ADMIN"
        pdf_bytes = await service.generate_invoice_pdf(
            invoice_id=invoice_id, requesting_tenant_id=tenant_id, is_super_admin=is_super_admin
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Facture-{invoice_id}.pdf"},
        )