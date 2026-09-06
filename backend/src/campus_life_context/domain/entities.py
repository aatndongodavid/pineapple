from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from campus_life_context.domain.value_objects import (
    ListingCategory,
    ListingStatus,
    MessageType,
    RideLocation,
    RideStatus,
)
from shared_kernel.domain.value_objects import Money


@dataclass
class MarketplaceListing:
    """Annonce sur la marketplace du campus."""
    id: UUID
    tenant_id: UUID
    seller_id: UUID
    title: str
    description: str
    price: Money
    category: ListingCategory
    status: ListingStatus
    image_urls: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RideShare:
    """Trajet de covoiturage proposé par un conducteur."""
    id: UUID
    tenant_id: UUID
    driver_id: UUID
    departure: RideLocation
    destination: RideLocation
    departure_time: datetime
    total_seats: int
    available_seats: int
    price_per_seat: Money
    passenger_ids: List[UUID] = field(default_factory=list)
    status: RideStatus = RideStatus.PLANNED

    def book_seat(self, passenger_id: UUID) -> None:
        """
        Réserve une place pour un passager.
        Lève une exception si le trajet n'est pas PLANNED ou s'il n'y a plus de place.
        """
        if self.status != RideStatus.PLANNED:
            raise ValueError("Cannot book a seat on a ride that is not PLANNED.")
        if self.available_seats <= 0:
            raise ValueError("No available seats left.")
        if passenger_id in self.passenger_ids:
            raise ValueError("Passenger already booked this ride.")
        if passenger_id == self.driver_id:
            raise ValueError("Driver cannot book their own ride.")

        self.passenger_ids.append(passenger_id)
        self.available_seats -= 1

    def cancel_booking(self, passenger_id: UUID) -> None:
        """
        Annule la réservation d'un passager.
        Lève une exception si le passager n'a pas réservé ce trajet.
        """
        if passenger_id not in self.passenger_ids:
            raise ValueError("Passenger has not booked this ride.")

        self.passenger_ids.remove(passenger_id)
        self.available_seats += 1


@dataclass
class Message:
    """Message envoyé dans une conversation."""
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    content: str
    message_type: MessageType
    sent_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Conversation:
    """Conversation entre plusieurs participants, rattachée à un contexte (marketplace, ride, etc.)."""
    id: UUID
    tenant_id: UUID
    participant_ids: List[UUID] = field(default_factory=list)
    context_type: Optional[str] = None       # ex: "MARKETPLACE", "RIDE", "GENERAL"
    context_id: Optional[UUID] = None        # identifiant de l'objet contexte
    last_message_at: Optional[datetime] = None

    def add_participant(self, user_id: UUID) -> None:
        """Ajoute un participant à la conversation s'il n'y est pas déjà."""
        if user_id not in self.participant_ids:
            self.participant_ids.append(user_id)

    def remove_participant(self, user_id: UUID) -> None:
        """Retire un participant de la conversation."""
        if user_id in self.participant_ids:
            self.participant_ids.remove(user_id)