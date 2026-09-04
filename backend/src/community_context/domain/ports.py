from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from community_context.domain.entities import Organization, Post, Room


class PostRepositoryPort(ABC):
    """Port de persistance pour l'agrégat Post."""

    @abstractmethod
    def save(self, post: Post) -> Post:
        """Sauvegarde une publication et retourne l'entité mise à jour."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, post_id: UUID) -> Optional[Post]:
        """Récupère une publication par son identifiant."""
        raise NotImplementedError

    @abstractmethod
    def list_feed(
        self,
        tenant_id: UUID,
        tab: str,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Post]:
        """
        Récupère le fil d'actualité pour un utilisateur donné.
        `tab` peut être : "for_you", "mon_etablissement", "mes_communautes", "academy",
        "opportunities", "marketplace".
        """
        raise NotImplementedError


class OrganizationRepositoryPort(ABC):
    """Port de persistance pour l'entité Organization."""

    @abstractmethod
    def save(self, org: Organization) -> Organization:
        """Sauvegarde une organisation."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, org_id: UUID, tenant_id: UUID) -> Optional[Organization]:
        """Récupère une organisation par son identifiant dans un tenant donné."""
        raise NotImplementedError

    @abstractmethod
    def list_by_tenant(self, tenant_id: UUID) -> List[Organization]:
        """Liste toutes les organisations d'un tenant."""
        raise NotImplementedError


class RoomRepositoryPort(ABC):
    """Port de persistance pour l'entité Room."""

    @abstractmethod
    def save(self, room: Room) -> Room:
        """Sauvegarde une salle."""
        raise NotImplementedError

    @abstractmethod
    def list_rooms(self, tenant_id: UUID) -> List[Room]:
        """Liste toutes les salles d'un tenant."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, room_id: UUID) -> Optional[Room]:
        """Récupère une salle par son identifiant."""
        raise NotImplementedError