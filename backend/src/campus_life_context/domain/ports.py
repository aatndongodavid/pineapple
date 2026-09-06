from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from campus_life_context.domain.entities import (
    Conversation,
    MarketplaceListing,
    Message,
    RideShare,
)
from campus_life_context.domain.value_objects import ListingCategory


class MarketplaceRepositoryPort(ABC):
    """Port de persistance pour les annonces de la marketplace."""

    @abstractmethod
    def save_listing(self, listing: MarketplaceListing) -> MarketplaceListing:
        """Sauvegarde une annonce et retourne l'entité mise à jour."""
        raise NotImplementedError

    @abstractmethod
    def get_listing_by_id(
        self, listing_id: UUID, tenant_id: UUID
    ) -> Optional[MarketplaceListing]:
        """Récupère une annonce par son identifiant dans un tenant donné."""
        raise NotImplementedError

    @abstractmethod
    def list_listings(
        self, tenant_id: UUID, category: Optional[ListingCategory]
    ) -> List[MarketplaceListing]:
        """Liste les annonces d'un tenant, filtrées éventuellement par catégorie."""
        raise NotImplementedError


class RideRepositoryPort(ABC):
    """Port de persistance pour les trajets de covoiturage."""

    @abstractmethod
    def save_ride(self, ride: RideShare) -> RideShare:
        """Sauvegarde un trajet et retourne l'entité mise à jour."""
        raise NotImplementedError

    @abstractmethod
    def get_ride_by_id(self, ride_id: UUID, tenant_id: UUID) -> Optional[RideShare]:
        """Récupère un trajet par son identifiant dans un tenant donné."""
        raise NotImplementedError

    @abstractmethod
    def search_rides(
        self, tenant_id: UUID, departure_query: Optional[str]
    ) -> List[RideShare]:
        """Recherche des trajets par adresse de départ (partielle ou complète)."""
        raise NotImplementedError


class MessagingRepositoryPort(ABC):
    """Port de persistance pour la messagerie interne."""

    @abstractmethod
    def get_or_create_conversation(
        self,
        tenant_id: UUID,
        participants: List[UUID],
        context_type: str,
        context_id: UUID,
    ) -> Conversation:
        """Récupère une conversation existante ou en crée une nouvelle."""
        raise NotImplementedError

    @abstractmethod
    def save_message(self, message: Message) -> Message:
        """Sauvegarde un message dans une conversation."""
        raise NotImplementedError

    @abstractmethod
    def list_messages(self, conversation_id: UUID, limit: int = 50) -> List[Message]:
        """Liste les messages d'une conversation (du plus récent au plus ancien)."""
        raise NotImplementedError