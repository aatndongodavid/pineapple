from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from campus_life_context.domain.value_objects import (
    ListingCategory,
    ListingStatus,
    MessageType,
    RideStatus,
)


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ListingCreateDTO(BaseDTO):
    title: str
    description: str
    price_fcfa: int
    category: ListingCategory
    image_urls: List[str] = []


class ListingResponseDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    seller_id: UUID
    title: str
    description: str
    price_fcfa: int
    category: ListingCategory
    status: ListingStatus
    image_urls: List[str]
    created_at: datetime


class RideCreateDTO(BaseDTO):
    departure_name: str
    destination_name: str
    departure_time: datetime
    total_seats: int
    price_per_seat_fcfa: int


class RideResponseDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    driver_id: UUID
    departure_name: str
    destination_name: str
    departure_time: datetime
    available_seats: int
    price_per_seat_fcfa: int
    passenger_ids: List[UUID]
    status: RideStatus


class SendMessageDTO(BaseDTO):
    conversation_id: UUID
    content: str
    message_type: MessageType = MessageType.TEXT


class MessageResponseDTO(BaseDTO):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    content: str
    message_type: MessageType
    sent_at: datetime