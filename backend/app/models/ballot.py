import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class EncryptedBallot(Base, TimestampMixin):
    __tablename__ = "encrypted_ballots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid
    )
    election_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("elections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    voter_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    encrypted_vote_payload: Mapped[str] = mapped_column(String(1024), nullable=False)
