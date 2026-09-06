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
from shared_kernel.infrastructure.database import AsyncSessionLocal
from shared_kernel.infrastructure.tenant_middleware import get_current_tenant_id

# ---------------------------------------------------------------------------
# Sécurité & dépendances transverses
# ---------------------------------------------------------------------------
security = HTTPBearer()


# NOTE: L'entité User doit contenir un champ `password_hash: str` pour stocker
#       le mot de passe haché. Ce champ est utilisé par le repository et les use cases.
#       Pensez à l'ajouter dans la définition de l'agrégat User.

# Dépendance pour obtenir la session factory (utilisée par les repositories)
async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return AsyncSessionLocal


# Dépendances pour les repositories
async def get_user_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresUserRepository:
    return PostgresUserRepository(session_factory)


async def get_cert_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresCertificationRepository:
    return PostgresCertificationRepository(session_factory)


# Dépendance pour le stockage de fichiers (à implémenter selon l'infra, ex: S3)
class DummyFileStorage(FileStoragePort):
    """Implémentation de démonstration - à remplacer par S3 en production."""

    async def upload_file(self, file_bytes: bytes, filename: str, mime_type: str) -> str:
        # Simule le téléversement et retourne une clé factice
        return f"dummy/{uuid.uuid4()}-{filename}"

    async def generate_presigned_url(self, file_key: str, expires_in: int = 3600) -> str:
        return f"https://example.com/{file_key}"


async def get_file_storage() -> FileStoragePort:
    # En production, utiliser S3FileStorage avec la config AWS
    return DummyFileStorage()


# Dépendance pour obtenir l'utilisateur courant à partir du JWT
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
) -> User:
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
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = await user_repo.get_by_id(user_id, tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


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
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Retourne le profil de l'utilisateur connecté avec son statut campus.
    """
    return UserResponseDTO(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        matricule=current_user.matricule,
        faculty=current_user.faculty,
        filiere=current_user.filiere,
        academic_year=current_user.academic_year,
        account_status=current_user.account_status,
        verification_status=current_user.verification_status,
        academic_status=current_user.academic_status,
        campus_status_display=current_user.resolve_campus_status().value,
    )


@router.post("/certification/submit", status_code=status.HTTP_202_ACCEPTED)
async def submit_certification(
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
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
            user_id=current_user.id,
            tenant_id=tenant_id,
            dto=CertificationSubmitDTO(
                document_type=document_type,
                file_base64_or_name=file.filename,
            ),
            file_bytes=file_bytes,
            original_filename=file.filename,
            mime_type=file.content_type,
        )
    except IdentityDomainError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"message": "Certification submitted successfully", "document_id": str(doc.id)}


@router.post("/certification/review", status_code=status.HTTP_200_OK)
async def review_certification(
    review: CertificationReviewDTO,
    current_user: User = Depends(get_current_user),  # Doit être un administrateur
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    user_repo: PostgresUserRepository = Depends(get_user_repo),
    cert_repo: PostgresCertificationRepository = Depends(get_cert_repo),
):
    """
    Validation ou rejet d'un document de certification (réservé aux admins).
    La vérification du rôle admin doit être implémentée selon le RBAC (A.15).
    """
    # TODO: Ajouter une vérification de rôle admin (ex: via un champ is_admin ou une table de rôles)
    use_case = ReviewCertificationUseCase(user_repo, cert_repo)
    try:
        await use_case.execute(
            admin_id=current_user.id,
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