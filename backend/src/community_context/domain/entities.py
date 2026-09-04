from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from community_context.domain.value_objects import (
    AudiencePolicy,
    OrganizationType,
    PostType,
    RoomStatus,
)


@dataclass
class Room:
    """Entité représentant une salle déclarée libre par un délégué."""
    id: UUID
    tenant_id: UUID
    name: str
    building: str
    status: RoomStatus
    declared_by_user_id: UUID
    expires_at: datetime

    def check_expiration(self, now: datetime) -> None:
        """
        Vérifie la validité de la déclaration de salle libre.
        Si le statut est FREE et que la date d'expiration est dépassée,
        repasse le statut à TO_CONFIRM.
        """
        if self.status == RoomStatus.FREE and now > self.expires_at:
            self.status = RoomStatus.TO_CONFIRM


@dataclass
class Organization:
    """Entité représentant un club, une association ou un mouvement."""
    id: UUID
    tenant_id: UUID
    name: str
    slug: str
    description: str
    type: OrganizationType
    logo_url: Optional[str]
    is_verified: bool
    owner_user_id: UUID


@dataclass
class Post:
    """
    Agrégat racine du contexte Community & Campus.
    Représente une publication dans le feed.
    """
    id: UUID
    tenant_id: UUID
    author_id: UUID
    type: PostType
    content: str
    audience_policy: AudiencePolicy
    organization_id: Optional[UUID] = None
    media_urls: List[str] = field(default_factory=list)
    is_sponsored: bool = False
    views_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def increment_views(self) -> None:
        """Incrémente le compteur de vues de la publication."""
        self.views_count += 1