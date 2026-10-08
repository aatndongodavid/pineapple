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
        raw_tid = payload.get("tid") or payload.get("tenant_id")
        token_tenant = uuid.UUID(raw_tid) if raw_tid else None
        if token_tenant and token_tenant != tenant_id:
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


# --- ENCAISSEMENT & WEBHOOKS (PHASE 3) ---

from fastapi import Request
from monetization_context.application.dtos import (
    ManualPaymentProofDTO,
    ManualProofCreateDTO,
    ManualProofReviewDTO,
    MobileMoneyPaymentDTO,
    PaymentAttemptDTO,
)
from monetization_context.application.services.payment_application_service import PaymentApplicationService
from monetization_context.infrastructure.adapters.fake_payment_provider import FakePaymentProviderAdapter


@router.post("/payments/manual-proof", response_model=ManualPaymentProofDTO, status_code=status.HTTP_201_CREATED)
async def submit_manual_payment_proof(
    dto: ManualProofCreateDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """Téléverser une preuve de virement / dépôt d'espèces pour règlement d'une facture."""
    async with session_factory() as session:
        service = PaymentApplicationService(session)
        return await service.submit_manual_proof(
            tenant_id=tenant_id,
            invoice_id=dto.invoice_id,
            file_path=dto.file_path,
            amount_declared_xaf=dto.amount_declared_xaf,
            payment_reference=dto.payment_reference,
        )


@router.post("/payments/manual-proof/{proof_id}/review", response_model=ManualPaymentProofDTO)
async def review_manual_payment_proof(
    proof_id: uuid.UUID,
    dto: ManualProofReviewDTO,
    current_user: dict = Depends(get_current_user),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """Validation / Rejet d'une preuve de paiement par le Super-Admin."""
    if current_user.get("user_type") != "PLATFORM_ADMIN":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Action réservée au Super-Admin")

    async with session_factory() as session:
        service = PaymentApplicationService(session)
        return await service.review_manual_proof(
            proof_id=proof_id,
            reviewer_user_id=current_user["user_id"],
            approve=dto.approve,
            rejection_reason=dto.rejection_reason,
        )


@router.post("/payments/mobile-money", response_model=PaymentAttemptDTO, status_code=status.HTTP_201_CREATED)
async def initiate_mobile_money_payment(
    dto: MobileMoneyPaymentDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """Initier un paiement Mobile Money (MTN MoMo / Orange Money) via agrégateur."""
    provider = FakePaymentProviderAdapter(webhook_secret=settings.JWT_SECRET_KEY)
    async with session_factory() as session:
        service = PaymentApplicationService(session, payment_provider=provider)
        return await service.initiate_mobile_money_payment(
            tenant_id=tenant_id,
            invoice_id=dto.invoice_id,
            phone_number=dto.phone_number,
            operator=dto.operator,
        )


@router.post("/webhooks/{provider_name}")
async def handle_payment_webhook(
    provider_name: str,
    request: Request,
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
):
    """Endpoint webhook dédié pour la notification serveur-à-serveur des paiements (Signature HMAC + Idempotence)."""
    payload_bytes = await request.body()
    signature_header = request.headers.get("X-Signature") or request.headers.get("X-Campay-Signature")
    secret = getattr(settings, f"{provider_name.upper()}_WEBHOOK_SECRET", settings.JWT_SECRET_KEY)

    provider = FakePaymentProviderAdapter(webhook_secret=secret)
    async with session_factory() as session:
        service = PaymentApplicationService(session, payment_provider=provider)
        return await service.process_webhook_payload(
            provider_name=provider_name.upper(),
            payload_bytes=payload_bytes,
            signature_header=signature_header,
            secret=secret,
        )
