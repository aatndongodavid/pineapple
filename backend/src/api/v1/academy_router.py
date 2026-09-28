import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from academy_context.application.dtos import (
    DocumentUploadDTO,
    DocumentResponseDTO,
    PurchaseRequestDTO,
    ReaderAccessDTO,
)
from academy_context.application.use_cases import (
    AccessDeniedError,
    DocumentNotFoundError,
    PaymentError,
    PurchasePremiumDocumentUseCase,
    StreamToPineappleReaderUseCase,
    UploadLibraryDocumentUseCase,
)
from academy_context.domain.entities import LibraryDocument, PremiumPurchase
from academy_context.domain.ports import (
    FileStoragePort,
    LibraryRepositoryPort,
    PurchaseRepositoryPort,
    WatermarkEnginePort,
)
from academy_context.domain.value_objects import AccessStatus, DocumentType, WatermarkMetadata
from academy_context.infrastructure.persistence.repositories import (
    PostgresLibraryRepository,
    PostgresPurchaseRepository,
    PyPDFWatermarkEngine,
)
from identity_context.infrastructure.persistence.repositories import PostgresUserRepository
from shared_kernel.config import settings
from shared_kernel.infrastructure.auth import get_current_user, require_role
from shared_kernel.infrastructure.database import AsyncSessionLocal
from shared_kernel.infrastructure.tenant_middleware import get_current_tenant_id

# ---------------------------------------------------------------------------
# Sécurité & dépendances transverses
# ---------------------------------------------------------------------------


class InMemoryFileStorage(FileStoragePort):
    """Stockage de fichiers en mémoire pour le développement (remplacer par S3 en prod)."""
    def __init__(self):
        self._storage = {}

    async def upload_file(self, file_bytes: bytes, filename: str, mime_type: str) -> str:
        file_key = f"{uuid.uuid4()}-{filename}"
        self._storage[file_key] = file_bytes
        return file_key

    async def get_file_bytes(self, file_key: str) -> bytes:
        return self._storage.get(file_key, b"")


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return AsyncSessionLocal


async def get_library_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresLibraryRepository:
    return PostgresLibraryRepository(session_factory)


async def get_purchase_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresPurchaseRepository:
    return PostgresPurchaseRepository(session_factory)


async def get_user_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresUserRepository:
    return PostgresUserRepository(session_factory)


async def get_file_storage() -> FileStoragePort:
    # En production, remplacer par S3FileStorage
    return InMemoryFileStorage()


async def get_watermark_engine() -> WatermarkEnginePort:
    return PyPDFWatermarkEngine()


async def get_user_reader_context(
    request: Request,
    current_user: dict = Depends(get_current_user),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
) -> dict:
    """Récupère le profil réel de l'utilisateur (dont son matricule) pour le filigrane Pineapple Reader."""
    user = await user_repo.get_by_id(current_user["user_id"], current_user["tenant_id"])
    matricule = user.matricule if user and user.matricule else "NON_MATRICULE"
    return {
        "user_id": current_user["user_id"],
        "tenant_id": current_user["tenant_id"],
        "role": current_user["role"],
        "matricule": matricule,
        "ip_address": request.client.host if request and request.client else "0.0.0.0",
    }


# ---------------------------------------------------------------------------
# Router principal
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/academy", tags=["Academy & Pineapple Reader"])


@router.get("/library", response_model=List[DocumentResponseDTO])
async def get_library(
    faculty: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    doc_type: Optional[DocumentType] = Query(None),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    library_repo: PostgresLibraryRepository = Depends(get_library_repo),
):
    """
    Explorer les documents académiques par filière/niveau/type.
    """
    docs = await library_repo.list_documents(tenant_id, faculty, level, doc_type)
    return [
        DocumentResponseDTO(
            id=doc.id,
            tenant_id=doc.tenant_id,
            title=doc.title,
            document_type=doc.document_type,
            faculty=doc.faculty,
            filiere=doc.filiere,
            academic_level=doc.academic_level,
            is_premium=doc.is_premium,
            price_fcfa=int(doc.price.amount),
            access_status=AccessStatus.PREMIUM_LOCKED if doc.is_premium else AccessStatus.FREE,
        )
        for doc in docs
    ]


@router.post("/library/upload", response_model=DocumentResponseDTO, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str = Form(...),
    document_type: DocumentType = Form(...),
    faculty: str = Form(...),
    filiere: str = Form(...),
    academic_level: str = Form(...),
    is_premium: bool = Form(False),
    price_fcfa: int = Form(0),
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role("ADMIN", "TEACHER")),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    library_repo: PostgresLibraryRepository = Depends(get_library_repo),
    file_storage: FileStoragePort = Depends(get_file_storage),
):
    """
    Proposer un document (Réservé aux Admins et Enseignants).
    """
    dto = DocumentUploadDTO(
        title=title,
        document_type=document_type,
        faculty=faculty,
        filiere=filiere,
        academic_level=academic_level,
        is_premium=is_premium,
        price_fcfa=price_fcfa,
    )
    file_bytes = await file.read()
    use_case = UploadLibraryDocumentUseCase(library_repo, file_storage)
    doc = await use_case.execute(
        tenant_id=tenant_id,
        uploader_id=current_user["user_id"],
        dto=dto,
        file_bytes=file_bytes,
        original_filename=file.filename or "document",
        mime_type=file.content_type or "application/pdf",
    )
    return DocumentResponseDTO(
        id=doc.id,
        tenant_id=doc.tenant_id,
        title=doc.title,
        document_type=doc.document_type,
        faculty=doc.faculty,
        filiere=doc.filiere,
        academic_level=doc.academic_level,
        is_premium=doc.is_premium,
        price_fcfa=int(doc.price.amount),
        access_status=AccessStatus.PREMIUM_LOCKED if doc.is_premium else AccessStatus.FREE,
    )


@router.post("/premium/purchase", response_model=dict)
async def purchase_premium(
    dto: PurchaseRequestDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    library_repo: PostgresLibraryRepository = Depends(get_library_repo),
    purchase_repo: PostgresPurchaseRepository = Depends(get_purchase_repo),
):
    """
    Acheter un corrigé premium.
    """
    use_case = PurchasePremiumDocumentUseCase(library_repo, purchase_repo)
    try:
        purchase = await use_case.execute(
            user_id=current_user["user_id"],
            tenant_id=tenant_id,
            dto=dto,
        )
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "message": "Purchase successful",
        "purchase_id": str(purchase.id),
        "document_id": str(purchase.document_id),
    }


@router.get("/reader/{document_id}/stream", response_class=Response)
async def stream_document(
    document_id: uuid.UUID,
    request: Request,
    user_ctx: dict = Depends(get_user_reader_context),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    library_repo: PostgresLibraryRepository = Depends(get_library_repo),
    purchase_repo: PostgresPurchaseRepository = Depends(get_purchase_repo),
    file_storage: FileStoragePort = Depends(get_file_storage),
    watermark_engine: WatermarkEnginePort = Depends(get_watermark_engine),
):
    """
    Flux de lecture sécurisé (Pineapple Reader) renvoyant le PDF filigrané à la volée.
    """
    use_case = StreamToPineappleReaderUseCase(
        library_repo=library_repo,
        purchase_repo=purchase_repo,
        file_storage=file_storage,
        watermark_engine=watermark_engine,
    )
    try:
        pdf_bytes = await use_case.execute(
            user_id=user_ctx["user_id"],
            tenant_id=tenant_id,
            document_id=document_id,
            user_matricule=user_ctx["matricule"],
            user_ip=user_ctx["ip_address"],
        )
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except AccessDeniedError:
        raise HTTPException(status_code=403, detail="Access denied")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=document.pdf"},
    )