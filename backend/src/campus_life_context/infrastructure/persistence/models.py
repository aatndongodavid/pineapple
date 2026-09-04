import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from campus_life_context.domain.value_objects import (
    ListingCategory,
    ListingStatus,
    MessageType,
    RideStatus,
)
from shared_kernel.infrastructure.database import Base


class MarketplaceListingModel(Base):
    __tablename__ = "marketplace_listings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    seller_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[ListingCategory] = mapped_column(
        Enum(ListingCategory, name="listing_category_enum"), nullable=False
    )
    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, name="listing_status_enum"),
        nullable=False,
        default=ListingStatus.ACTIVE,
    )
    image_urls: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RideShareModel(Base):
    __tablename__ = "rideshares"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    driver_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    departure_name: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_name: Mapped[str] = mapped_column(String(255), nullable=False)
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    available_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_seat: Mapped[int] = mapped_column(Integer, nullable=False)
    passenger_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[RideStatus] = mapped_column(
        Enum(RideStatus, name="ride_status_enum"),
        nullable=False,
        default=RideStatus.PLANNED,
    )


class ConversationModel(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    participant_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    context_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    context_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType, name="message_type_enum"),
        nullable=False,
        default=MessageType.TEXT,
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )