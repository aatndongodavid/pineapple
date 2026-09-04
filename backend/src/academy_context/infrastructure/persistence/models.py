import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from democracy_context.domain.entities import ElectionStatus, MovementStatus
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
    eligibility_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
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
    status: Mapped[MovementStatus] = mapped_column(
        Enum(MovementStatus, name="movement_status_enum"),
        nullable=False,
        default=MovementStatus.APPROVED,
    )


class BallotModel(Base):
    __tablename__ = "ballots"
    __table_args__ = (
        UniqueConstraint("election_id", "voter_hash", name="uq_ballot_voter_per_election"),
        Index("ix_ballots_election_id", "election_id"),
        Index("ix_ballots_tenant_id", "tenant_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    election_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("elections.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    voter_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_vote: Mapped[str] = mapped_column(Text, nullable=False)
    cast_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )