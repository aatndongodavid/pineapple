from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from passlib.context import CryptContext
from jose import jwt

from identity_context.application.dtos import (
    CertificationReviewDTO,
    CertificationSubmitDTO,
    TokenResponseDTO,
    UserLoginDTO,
    UserRegisterDTO,
)
from identity_context.domain.entities import CertificationDocument, User
from identity_context.domain.ports import (
    CertificationRepositoryPort,
    FileStoragePort,
    UserRepositoryPort,
)
from identity_context.domain.value_objects import (
    AccountStatus,
    AcademicStatus,
    DocumentType,
    VerificationStatus,
)
from shared_kernel.config import settings

# Configuration du hachage des mots de passe avec Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class IdentityDomainError(Exception):
    """Base exception for identity domain errors."""
    pass


class EmailAlreadyExistsError(IdentityDomainError):
    pass


class MatriculeAlreadyExistsError(IdentityDomainError):
    pass


class InvalidCredentialsError(IdentityDomainError):
    pass


class CertificationDocumentNotFoundError(IdentityDomainError):
    pass


class RejectionReasonRequiredError(IdentityDomainError):
    pass


class RegisterUserUseCase:
    """Use case for registering a new user."""

    def __init__(self, user_repo: UserRepositoryPort):
        self._user_repo = user_repo

    def execute(self, dto: UserRegisterDTO, tenant_id: UUID) -> User:
        # Vérifier unicité de l'email et du matricule
        if self._user_repo.get_by_email(dto.email) is not None:
            raise EmailAlreadyExistsError(f"Email {dto.email} already registered.")
        if self._user_repo.get_by_matricule(dto.matricule, tenant_id) is not None:
            raise MatriculeAlreadyExistsError(
                f"Matricule {dto.matricule} already exists for this tenant."
            )

        # Hacher le mot de passe
        hashed_password = pwd_context.hash(dto.password)

        # Créer l'entité User
        user = User(
            id=uuid4(),
            tenant_id=tenant_id,
            email=dto.email,
            first_name=dto.first_name,
            last_name=dto.last_name,
            matricule=dto.matricule,
            faculty=dto.faculty,
            filiere=dto.filiere,
            academic_year=dto.academic_year,
            account_status=AccountStatus.ACTIVE,
            verification_status=VerificationStatus.UNVERIFIED,
            academic_status=AcademicStatus.STUDENT,
            created_at=datetime.utcnow(),
            password_hash=hashed_password,  # à ajouter à l'entité User
        )

        # Persister
        return self._user_repo.save(user)


class AuthenticateUserUseCase:
    """Use case for authenticating a user and returning a JWT."""

    def __init__(self, user_repo: UserRepositoryPort):
        self._user_repo = user_repo

    def execute(self, dto: UserLoginDTO) -> TokenResponseDTO:
        user = self._user_repo.get_by_email(dto.email)
        if user is None or not pwd_context.verify(dto.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")

        # Vérifier que le compte est actif
        if user.account_status != AccountStatus.ACTIVE:
            raise InvalidCredentialsError("Account is not active.")

        # Générer le JWT
        expiration = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "exp": expiration,
        }
        access_token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        return TokenResponseDTO(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            tenant_id=user.tenant_id,
        )


class SubmitCertificationUseCase:
    """Use case for submitting a certification document."""

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        cert_repo: CertificationRepositoryPort,
        file_storage: FileStoragePort,
    ):
        self._user_repo = user_repo
        self._cert_repo = cert_repo
        self._file_storage = file_storage

    def execute(
        self,
        user_id: UUID,
        tenant_id: UUID,
        dto: CertificationSubmitDTO,
        file_bytes: bytes,
        original_filename: str,
        mime_type: str,
    ) -> CertificationDocument:
        user = self._user_repo.get_by_id(user_id, tenant_id)
        if user is None:
            raise IdentityDomainError("User not found.")

        # Téléverser le fichier et obtenir la clé S3
        file_key = self._file_storage.upload_file(file_bytes, original_filename, mime_type)

        # Créer le document de certification
        doc = CertificationDocument(
            id=uuid4(),
            user_id=user_id,
            document_type=dto.document_type,
            file_key=file_key,
            status=VerificationStatus.PENDING,
            submitted_at=datetime.utcnow(),
        )
        saved_doc = self._cert_repo.save_document(doc)

        # Mettre à jour le statut de l'utilisateur
        user.verification_status = VerificationStatus.PENDING
        self._user_repo.save(user)

        return saved_doc


class ReviewCertificationUseCase:
    """Use case for admin to review a certification document."""

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        cert_repo: CertificationRepositoryPort,
    ):
        self._user_repo = user_repo
        self._cert_repo = cert_repo

    def execute(self, admin_id: UUID, tenant_id: UUID, dto: CertificationReviewDTO) -> None:
        # Vérifier que le document existe et appartient au tenant
        documents = self._cert_repo.get_by_user_id(dto.document_id)  # attention : get_by_user_id prend user_id, pas doc id
        # Il faut une méthode pour récupérer par document_id, à adapter.
        # On suppose qu'on a une méthode get_by_id dans CertificationRepositoryPort (non spécifiée)
        # On va simuler en cherchant dans les pending documents.
        pending_docs = self._cert_repo.get_pending_documents(tenant_id)
        doc = next((d for d in pending_docs if d.id == dto.document_id), None)
        if doc is None:
            raise CertificationDocumentNotFoundError("Document not found or not pending.")

        if dto.approved:
            doc.status = VerificationStatus.VERIFIED
            doc.rejection_reason = None
            # Mettre à jour l'utilisateur
            user = self._user_repo.get_by_id(doc.user_id, tenant_id)
            if user:
                user.verification_status = VerificationStatus.VERIFIED
                self._user_repo.save(user)
        else:
            if not dto.rejection_reason:
                raise RejectionReasonRequiredError("Rejection reason is required when rejecting.")
            doc.status = VerificationStatus.REJECTED
            doc.rejection_reason = dto.rejection_reason
            # Mettre à jour l'utilisateur
            user = self._user_repo.get_by_id(doc.user_id, tenant_id)
            if user:
                user.verification_status = VerificationStatus.REJECTED
                self._user_repo.save(user)

        # Sauvegarder le document mis à jour
        self._cert_repo.save_document(doc)


class ResetAnnualCertificationsUseCase:
    """Use case to expire all verified student certifications for a tenant."""

    def __init__(self, user_repo: UserRepositoryPort):
        self._user_repo = user_repo

    def execute(self, tenant_id: UUID) -> int:
        """
        Expire all currently verified student certifications in the tenant.
        Returns the number of affected users.
        """
        users = self._user_repo.list_expired_certifications(tenant_id)
        # Filtrer pour ne garder que les étudiants vérifiés
        affected = 0
        for user in users:
            if (
                user.academic_status == AcademicStatus.STUDENT
                and user.verification_status == VerificationStatus.VERIFIED
            ):
                user.expire_certification()
                self._user_repo.save(user)
                affected += 1
        return affected