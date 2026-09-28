import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_context.application.dtos import (
    CertificationReviewDTO,
    CertificationSubmitDTO,
    TokenResponseDTO,
    UserLoginDTO,
    UserRegisterDTO,
    UserResponseDTO,
)
from identity_context.application.use_cases import (
    AuthenticateUserUseCase,
    CertificationDocumentNotFoundError,
    EmailAlreadyExistsError,
    IdentityDomainError,
    InvalidCredentialsError,
    MatriculeAlreadyExistsError,
    RegisterUserUseCase,
    RejectionReasonRequiredError,
    ReviewCertificationUseCase,
    SubmitCertificationUseCase,
)
from identity_context.domain.entities import User
from identity_context.domain.ports import (
    CertificationRepositoryPort,
    FileStoragePort,
    UserRepositoryPort,
)
from identity_context.domain.value_objects import DocumentType
from identity_context.infrastructure.persistence.repositories import (
    PostgresCertificationRepository,
    PostgresUserRepository,
)
from shared_kernel.config import settings
from shared_kernel.infrastructure.auth import get_current_user, require_role
from shared_kernel.infrastructure.database import AsyncSessionLocal
from shared_kernel.infrastructure.tenant_middleware import get_current_tenant_id


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return AsyncSessionLocal


async def get_user_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresUserRepository:
    return PostgresUserRepository(session_factory)


async def get_cert_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresCertificationRepository:
    return PostgresCertificationRepository(session_factory)


class DummyFileStorage(FileStoragePort):
    def upload_file(self, file_bytes: bytes, original_filename: str, mime_type: str) -> str:
        return f"dummy_key_{uuid.uuid4().hex}"

    async def generate_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        return f"https://example.com/{file_key}"


async def get_file_storage() -> FileStoragePort:
    return DummyFileStorage()


# ---------------------------------------------------------------------------
# Router principal
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/identity", tags=["Identity & Pineapple ID"])


@router.post("/register", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
async def register(
    dto: UserRegisterDTO,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
):
    """
    Inscription d'un nouvel utilisateur.
    Le tenant_id provient du header X-Tenant-ID.
    """
    use_case = RegisterUserUseCase(user_repo)
    try:
        user = await use_case.execute(dto, tenant_id)
    except EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    except MatriculeAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Matricule already exists for this institution",
        )

    return UserResponseDTO(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        matricule=user.matricule,
        faculty=user.faculty,
        filiere=user.filiere,
        academic_year=user.academic_year,
        account_status=user.account_status,
        verification_status=user.verification_status,
        academic_status=user.academic_status,
        campus_status_display=user.resolve_campus_status().value,
    )


@router.post("/login", response_model=TokenResponseDTO)
async def login(
    dto: UserLoginDTO,
    user_repo: PostgresUserRepository = Depends(get_user_repo),
):
    """
    Authentification et émission du JWT.
    """
    use_case = AuthenticateUserUseCase(user_repo)
    try:
        token_dto = await use_case.execute(dto)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return token_dto


@router.get("/me", response_model=UserResponseDTO)
async def get_me(
    current_user: dict = Depends(get_current_user),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
):
    """
    Retourne le profil de l'utilisateur connecté avec son statut campus et son rôle.
    """
    user = await user_repo.get_by_id(current_user["user_id"], current_user["tenant_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé",
        )
    return UserResponseDTO(
        id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        matricule=user.matricule,
        faculty=user.faculty,
        filiere=user.filiere,
        academic_year=user.academic_year,
        account_status=user.account_status,
        verification_status=user.verification_status,
        academic_status=user.academic_status,
        role=user.role,
        campus_status_display=user.resolve_campus_status().value,
    )


@router.post("/certification/submit", status_code=status.HTTP_202_ACCEPTED)
async def submit_certification(
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
    cert_repo: PostgresCertificationRepository = Depends(get_cert_repo),
    file_storage: FileStoragePort = Depends(get_file_storage),
):
    """
    Soumission d'un justificatif pour la certification annuelle.
    Le fichier est téléversé et le statut utilisateur passe en PENDING.
    """
    file_bytes = await file.read()
    use_case = SubmitCertificationUseCase(user_repo, cert_repo, file_storage)
    try:
        doc = await use_case.execute(
            user_id=current_user["user_id"],
            tenant_id=tenant_id,
            dto=CertificationSubmitDTO(
                document_type=document_type,
                file_base64_or_name=file.filename or "document",
            ),
            file_bytes=file_bytes,
            original_filename=file.filename or "document",
            mime_type=file.content_type or "application/octet-stream",
        )
    except IdentityDomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"message": "Certification submitted successfully", "document_id": str(doc.id)}


@router.post("/certification/review", status_code=status.HTTP_200_OK)
async def review_certification(
    review: CertificationReviewDTO,
    admin: dict = Depends(require_role("ADMIN")),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
    cert_repo: PostgresCertificationRepository = Depends(get_cert_repo),
):
    """
    Validation ou rejet d'un document de certification (réservé aux administrateurs).
    """
    use_case = ReviewCertificationUseCase(user_repo, cert_repo)
    try:
        await use_case.execute(
            admin_id=admin["user_id"],
            tenant_id=tenant_id,
            dto=review,
        )
    except CertificationDocumentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification document not found or not pending",
        )
    except RejectionReasonRequiredError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required when rejecting a document",
        )
    return {"message": "Certification review processed"}