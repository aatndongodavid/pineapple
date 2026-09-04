from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from identity_context.domain.entities import CertificationDocument, User
from identity_context.domain.ports import CertificationRepositoryPort, UserRepositoryPort
from identity_context.domain.value_objects import (
    AccountStatus,
    AcademicStatus,
    VerificationStatus,
)
from identity_context.infrastructure.persistence.models import (
    CertificationDocumentModel,
    UserModel,
)


class PostgresUserRepository(UserRepositoryPort):
    """Implémentation PostgreSQL du port UserRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_model(user: User) -> UserModel:
        """Convertit une entité User en modèle ORM UserModel."""
        return UserModel(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            hashed_password=getattr(user, "password_hash", ""),  # Supposé présent
            first_name=user.first_name,
            last_name=user.last_name,
            matricule=user.matricule,
            faculty=user.faculty,
            filiere=user.filiere,
            academic_year=user.academic_year,
            account_status=user.account_status,
            verification_status=user.verification_status,
            academic_status=user.academic_status,
            created_at=user.created_at,
        )

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        """Convertit un modèle ORM en entité User."""
        user = User(
            id=model.id,
            tenant_id=model.tenant_id,
            email=model.email,
            first_name=model.first_name,
            last_name=model.last_name,
            matricule=model.matricule,
            faculty=model.faculty,
            filiere=model.filiere,
            academic_year=model.academic_year,
            account_status=model.account_status,
            verification_status=model.verification_status,
            academic_status=model.academic_status,
            created_at=model.created_at,
        )
        # Ajouter password_hash si l'entité le possède
        if hasattr(user, "password_hash"):
            user.password_hash = model.hashed_password
        return user

    async def save(self, user: User) -> User:
        async with self._session_factory() as session:
            model = self._to_model(user)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return user

    async def get_by_id(self, user_id: UUID, tenant_id: UUID) -> Optional[User]:
        async with self._session_factory() as session:
            stmt = select(UserModel).where(
                UserModel.id == user_id,
                UserModel.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        async with self._session_factory() as session:
            stmt = select(UserModel).where(UserModel.email == email)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def get_by_matricule(self, matricule: str, tenant_id: UUID) -> Optional[User]:
        async with self._session_factory() as session:
            stmt = select(UserModel).where(
                UserModel.matricule == matricule,
                UserModel.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def list_expired_certifications(self, tenant_id: UUID) -> List[User]:
        """
        Retourne tous les étudiants certifiés (VERIFIED) du tenant,
        qui sont donc candidats à l'expiration.
        """
        async with self._session_factory() as session:
            stmt = select(UserModel).where(
                UserModel.tenant_id == tenant_id,
                UserModel.verification_status == VerificationStatus.VERIFIED,
                UserModel.academic_status == AcademicStatus.STUDENT,
            )
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]


class PostgresCertificationRepository(CertificationRepositoryPort):
    """Implémentation PostgreSQL du port CertificationRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_model(doc: CertificationDocument) -> CertificationDocumentModel:
        return CertificationDocumentModel(
            id=doc.id,
            user_id=doc.user_id,
            document_type=doc.document_type,
            file_key=doc.file_key,
            status=doc.status,
            rejection_reason=doc.rejection_reason,
            submitted_at=doc.submitted_at,
        )

    @staticmethod
    def _to_entity(model: CertificationDocumentModel) -> CertificationDocument:
        return CertificationDocument(
            id=model.id,
            user_id=model.user_id,
            document_type=model.document_type,
            file_key=model.file_key,
            status=model.status,
            rejection_reason=model.rejection_reason,
            submitted_at=model.submitted_at,
        )

    async def save_document(self, doc: CertificationDocument) -> CertificationDocument:
        async with self._session_factory() as session:
            model = self._to_model(doc)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return doc

    async def get_pending_documents(self, tenant_id: UUID) -> List[CertificationDocument]:
        async with self._session_factory() as session:
            stmt = (
                select(CertificationDocumentModel)
                .join(UserModel, CertificationDocumentModel.user_id == UserModel.id)
                .where(
                    UserModel.tenant_id == tenant_id,
                    CertificationDocumentModel.status == VerificationStatus.PENDING,
                )
            )
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]

    async def get_by_user_id(self, user_id: UUID) -> List[CertificationDocument]:
        async with self._session_factory() as session:
            stmt = select(CertificationDocumentModel).where(
                CertificationDocumentModel.user_id == user_id
            )
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]