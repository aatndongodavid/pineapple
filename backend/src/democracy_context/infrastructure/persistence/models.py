import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

JSONBType = JSON().with_variant(JSONB, "postgresql")

from democracy_context.domain.entities import ElectionStatus
from shared_kernel.infrastructure.database import Base


class ElectionModel(Base):
    __tablename__ = "elections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    election_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ElectionStatus] = mapped_column(
        Enum(ElectionStatus, name="election_status_enum"),
        nullable=False,
        default=ElectionStatus.DRAFT,
    )
    eligibility_rules: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    config: Mapped[dict] = mapped_column(JSONBType, nullable=False, default=dict)
    voting_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    voting_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MovementModel(Base):
    __tablename__ = "movements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    election_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("elections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slogan: Mapped[str] = mapped_column(String(300), nullable=False)
    program_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="APPROVED")


class VoteModel(Base):
    __tablename__ = "votes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    election_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    voter_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_vote: Mapped[str] = mapped_column(Text, nullable=False)
    cast_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DemocracyAuditLogModel(Base):
    __tablename__ = "democracy_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONBType, nullable=False, default=dict)
    hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
