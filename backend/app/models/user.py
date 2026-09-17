import enum
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.feed import Post, Comment, Reaction


class AccountStatus(str, enum.Enum):
    ACCOUNT = "ACCOUNT"
    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class AcademicStatus(str, enum.Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ALUMNI = "ALUMNI"
    ADMIN = "ADMIN"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    account_status: Mapped[AccountStatus] = mapped_column(
        SQLEnum(AccountStatus),
        default=AccountStatus.ACCOUNT,
        nullable=False
    )
    academic_status: Mapped[AcademicStatus] = mapped_column(
        SQLEnum(AcademicStatus),
        default=AcademicStatus.STUDENT,
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    certification_requests: Mapped[List["CertificationRequest"]] = relationship(
        "CertificationRequest", back_populates="user", cascade="all, delete-orphan"
    )
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    reactions: Mapped[List["Reaction"]] = relationship("Reaction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User email={self.email} status={self.account_status}>"


class CertificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class CertificationRequest(Base, TimestampMixin):
    __tablename__ = "certification_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id_number: Mapped[str] = mapped_column(String(100), nullable=False)
    document_url: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[CertificationStatus] = mapped_column(
        SQLEnum(CertificationStatus),
        default=CertificationStatus.PENDING,
        nullable=False
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="certification_requests")
