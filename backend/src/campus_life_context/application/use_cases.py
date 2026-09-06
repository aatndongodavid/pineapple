from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol, Optional
from uuid import UUID, uuid4

from campus_life_context.application.dtos import (
    ListingCreateDTO,
    MessageResponseDTO,
    RideCreateDTO,
    SendMessageDTO,
)
from campus_life_context.domain.entities import Conversation, MarketplaceListing, Message, RideShare
from campus_life_context.domain.ports import MarketplaceRepositoryPort, MessagingRepositoryPort, RideRepositoryPort
from campus_life_context.domain.value_objects import (
    ListingCategory,
    ListingStatus,
    MessageType,
    RideLocation,
    RideStatus,
)
from shared_kernel.domain.value_objects import Money


# --- Exceptions métier ---
class UserNotEligibleError(Exception):
    """L'utilisateur n'est pas autorisé à effectuer cette action."""
    pass

class RideNotFoundError(Exception):
    pass

class RideNotAvailableError(Exception):
    pass

class AlreadyBookedError(Exception):
    pass


# --- Protocole pour vérifier le statut de certification (dépendance transversale) ---
class UserStatusProvider(Protocol):
    """Fournit le statut de certification d'un utilisateur."""
    async def is_certified_active(self, user_id: UUID) -> bool:
        ...


class CreateMarketplaceListingUseCase:
    """Création d'une annonce marketplace, réservée aux étudiants certifiés actifs."""

    def __init__(
        self,
        marketplace_repo: MarketplaceRepositoryPort,
        user_status_provider: UserStatusProvider,
    ):
        self._marketplace_repo = marketplace_repo
        self._user_status_provider = user_status_provider

    async def execute(
        self,
        seller_id: UUID,
        tenant_id: UUID,
        dto: ListingCreateDTO,
    ) -> MarketplaceListing:
        # Vérification du statut de l'utilisateur
        if not await self._user_status_provider.is_certified_active(seller_id):
            raise UserNotEligibleError("Seuls les étudiants certifiés actifs peuvent publier une annonce.")

        listing = MarketplaceListing(
            id=uuid4(),
            tenant_id=tenant_id,
            seller_id=seller_id,
            title=dto.title,
            description=dto.description,
            price=Money(amount=Decimal(dto.price_fcfa), currency="XAF"),
            category=dto.category,
            status=ListingStatus.ACTIVE,
            image_urls=dto.image_urls,
            created_at=datetime.utcnow(),
        )

        return await self._marketplace_repo.save_listing(listing)


class CreateRideShareUseCase:
    """Création d'une offre de covoiturage Pineapple Ride."""

    def __init__(self, ride_repo: RideRepositoryPort):
        self._ride_repo = ride_repo

    async def execute(
        self,
        driver_id: UUID,
        tenant_id: UUID,
        dto: RideCreateDTO,
    ) -> RideShare:
        ride = RideShare(
            id=uuid4(),
            tenant_id=tenant_id,
            driver_id=driver_id,
            departure=RideLocation(address_name=dto.departure_name),
            destination=RideLocation(address_name=dto.destination_name),
            departure_time=dto.departure_time,
            total_seats=dto.total_seats,
            available_seats=dto.total_seats,
            price_per_seat=Money(amount=Decimal(dto.price_per_seat_fcfa), currency="XAF"),
            passenger_ids=[],
            status=RideStatus.PLANNED,
        )

        return await self._ride_repo.save_ride(ride)


class BookRideSeatUseCase:
    """Réservation d'une place dans un trajet."""

    def __init__(self, ride_repo: RideRepositoryPort):
        self._ride_repo = ride_repo

    async def execute(
        self,
        passenger_id: UUID,
        tenant_id: UUID,
        ride_id: UUID,
    ) -> RideShare:
        ride = await self._ride_repo.get_ride_by_id(ride_id, tenant_id)
        if not ride:
            raise RideNotFoundError("Trajet introuvable.")

        try:
            ride.book_seat(passenger_id)
        except ValueError as e:
            # Transformer les erreurs de validation en exceptions métier
            if "not PLANNED" in str(e):
                raise RideNotAvailableError("Le trajet n'est pas disponible pour réservation.")
            if "No available seats" in str(e):
                raise RideNotAvailableError("Plus de places disponibles.")
            if "already booked" in str(e):
                raise AlreadyBookedError("Le passager a déjà réservé ce trajet.")
            if "Driver cannot book" in str(e):
                raise UserNotEligibleError("Le conducteur ne peut pas réserver son propre trajet.")
            raise

        return await self._ride_repo.save_ride(ride)


class SendTransversalMessageUseCase:
    """
    Service unique de messagerie interne, réutilisable par tous les modules
    (Marketplace, Ride, Projets, etc.).
    """

    def __init__(self, messaging_repo: MessagingRepositoryPort):
        self._messaging_repo = messaging_repo

    async def execute(
        self,
        sender_id: UUID,
        tenant_id: UUID,
        dto: SendMessageDTO,
    ) -> MessageResponseDTO:
        # La conversation doit exister ; on suppose qu'elle a été créée au préalable
        # (par exemple via get_or_create_conversation dans un autre use case).
        # Ici on crée simplement le message et on le sauvegarde.
        message = Message(
            id=uuid4(),
            conversation_id=dto.conversation_id,
            sender_id=sender_id,
            content=dto.content,
            message_type=dto.message_type,
            sent_at=datetime.utcnow(),
        )

        saved_message = await self._messaging_repo.save_message(message)

        # Mise à jour éventuelle de la conversation (non implémentée dans le port,
        # on peut l'ajouter si nécessaire)
        # On retourne le DTO de réponse
        return MessageResponseDTO(
            id=saved_message.id,
            conversation_id=saved_message.conversation_id,
            sender_id=saved_message.sender_id,
            content=saved_message.content,
            message_type=saved_message.message_type,
            sent_at=saved_message.sent_at,
        )