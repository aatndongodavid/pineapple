import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from identity_context.domain.value_objects import (
    AccountStatus,
    AcademicStatus,
    DocumentType,
    VerificationStatus,
)
from shared_kernel.infrastructure.database import Base


class UserModel(Base):
    """Identité globale d'un utilisateur dans la plateforme Pineapple."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_type: Mapped[str] = mapped_column(String(50), default="STANDARD", nullable=False)  # STANDARD, ENTERPRISE, PLATFORM_ADMIN

    account_status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="account_status_enum"), nullable=False, default=AccountStatus.ACTIVE
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status_enum"),
        nullable=False,
        default=VerificationStatus.UNVERIFIED,
    )

    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TenantModel(Base):
    """Établissement (école/université) abonnée à Pineapple."""
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    enrollment_mode: Mapped[str] = mapped_column(String(50), default="BOTH", nullable=False)  # SELF_CLAIM, INVITATION, BOTH
    auto_approve_claims: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    current_academic_year: Mapped[str] = mapped_column(String(20), default="2026-2027", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Africa/Douala", nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="Cameroun", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TenantSubscriptionModel(Base):
    """Abonnement d'un établissement."""
    __tablename__ = "tenant_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="STANDARD", nullable=False)  # FREE_TRIAL, STANDARD, PREMIUM
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # TRIAL, ACTIVE, PAST_DUE, SUSPENDED, EXPIRED
    seats_limit: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    grace_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    payment_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ClassGroupModel(Base):
    """Classe / Promotion au sein d'un établissement (ex: GIT 3)."""
    __tablename__ = "class_groups"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", "academic_year", name="uq_class_group_code_year"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    faculty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    filiere: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ImportBatchModel(Base):
    """Lot d'import de registre."""
    __tablename__ = "import_batches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class RosterEntryModel(Base):
    """Registre officiel des étudiants saisi/importé par l'administration."""
    __tablename__ = "roster_entries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "matricule", "academic_year", name="uq_roster_matricule_year"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    matricule: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[str] = mapped_column(String(255), nullable=False)  # Chiffré au repos
    birth_place: Mapped[str] = mapped_column(String(255), nullable=False)  # Chiffré au repos

    # Colonnes normalisées pour la comparaison d'auto-rattachement Mode A
    norm_matricule: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    norm_first_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    norm_last_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    norm_birth_date: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    norm_birth_place: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    class_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("class_groups.id", ondelete="SET NULL"), nullable=True)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    official_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="NOT_CLAIMED", nullable=False)  # NOT_CLAIMED, INVITED, CLAIMED, REVOKED

    claimed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    import_batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MembershipModel(Base):
    """Appartenance d'un utilisateur à un établissement."""
    __tablename__ = "memberships"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    roster_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("roster_entries.id", ondelete="SET NULL"), unique=True, nullable=True)
    class_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("class_groups.id", ondelete="SET NULL"), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="STUDENT", nullable=False)  # STUDENT, TEACHER, STAFF, TENANT_ADMIN
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # PENDING, ACTIVE, SUSPENDED, ENDED
    joined_via: Mapped[str] = mapped_column(String(50), default="CLAIM", nullable=False)  # CLAIM, INVITATION, ADMIN
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)


class InvitationModel(Base):
    """Invitation Mode B générée par l'école."""
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    roster_entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roster_entries.id", ondelete="CASCADE"), index=True, nullable=False)
    identifier: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_sent_to: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, USED, EXPIRED, REVOKED
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    last_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EnrollmentAttemptModel(Base):
    """Journal de tentatives de rattachement pour anti-bruteforce et audit."""
    __tablename__ = "enrollment_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ip: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # CLAIM, ACTIVATE
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)


class ClassDelegateModel(Base):
    """Délégué de classe désigné par l'administration."""
    __tablename__ = "class_delegates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    class_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(50), default="TITULAIRE", nullable=False)  # TITULAIRE, SUPPLEANT
    appointed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    appointed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)


class CertificationDocumentModel(Base):
    __tablename__ = "certification_documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type_enum"), nullable=False
    )
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status_enum"),
        nullable=False,
        default=VerificationStatus.PENDING,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )