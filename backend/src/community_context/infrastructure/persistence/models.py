import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from community_context.domain.value_objects import (
    AudienceScope,
    OrganizationType,
    PostType,
    RoomStatus,
)
from shared_kernel.infrastructure.database import Base


class PostModel(Base):
    __tablename__ = "publications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[PostType] = mapped_column(
        Enum(PostType, name="post_type_enum"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    media_urls: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    scope: Mapped[AudienceScope] = mapped_column(
        Enum(AudienceScope, name="audience_scope_enum"), nullable=False
    )
    is_sponsored: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class OrganizationModel(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[OrganizationType] = mapped_column(
        Enum(OrganizationType, name="organization_type_enum"), nullable=False
    )
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)


class RoomModel(Base):
    """Salle physique (ex: Amphi 500)."""
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    building: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    status: Mapped[RoomStatus] = mapped_column(
        Enum(RoomStatus, name="room_status_enum"), default=RoomStatus.FREE, nullable=False
    )
    declared_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    class_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("class_groups.id", ondelete="SET NULL"), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class RoomStatusDeclarationModel(Base):
    """Historique des déclarations d'état d'une salle par un délégué."""
    __tablename__ = "room_status_declarations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True, nullable=False)
    class_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("class_groups.id", ondelete="SET NULL"), nullable=True)
    declared_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[RoomStatus] = mapped_column(Enum(RoomStatus, name="room_status_enum"), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    declared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ClassAnnouncementModel(Base):
    """Annonces de classe créées par un délégué."""
    __tablename__ = "class_announcements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    class_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ClassIncidentModel(Base):
    """Signalement d'incident par un délégué (absence enseignant, cours annulé, problème matériel...)."""
    __tablename__ = "class_incidents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    class_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="TEACHER_ABSENT", nullable=False)  # TEACHER_ABSENT, COURSE_CANCELLED, ROOM_ISSUE, REQUEST, OTHER
    status: Mapped[str] = mapped_column(String(50), default="OPEN", nullable=False)  # OPEN, ACKNOWLEDGED, RESOLVED
    reported_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ClassPollModel(Base):
    """Sondage de classe."""
    __tablename__ = "class_polls"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    class_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    question: Mapped[str] = mapped_column(String(300), nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ClassPollOptionModel(Base):
    """Options de réponse à un sondage de classe."""
    __tablename__ = "class_poll_options"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    poll_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_polls.id", ondelete="CASCADE"), index=True, nullable=False)
    option_text: Mapped[str] = mapped_column(String(200), nullable=False)
    vote_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ClassPollVoteModel(Base):
    """Vote d'un membre de classe sur un sondage."""
    __tablename__ = "class_poll_votes"
    __table_args__ = (
        UniqueConstraint("poll_id", "user_id", name="uq_class_poll_user_vote"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    poll_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_polls.id", ondelete="CASCADE"), index=True, nullable=False)
    option_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_poll_options.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    voted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ClassEventModel(Base):
    """Événement ou échéance de classe."""
    __tablename__ = "class_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    class_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("class_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), default="EVENT", nullable=False)  # EXAM, ASSIGNMENT, EVENT
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)