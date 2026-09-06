from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from community_context.application.dtos import (
    OrganizationCreateDTO,
    PostCreateDTO,
    RoomDeclareDTO,
)
from community_context.domain.entities import Organization, Post, Room
from community_context.domain.ports import (
    OrganizationRepositoryPort,
    PostRepositoryPort,
    RoomRepositoryPort,
)
from community_context.domain.value_objects import (
    AudiencePolicy,
    AudienceScope,
    PostType,
    RoomStatus,
)


class PostNotFoundError(Exception):
    pass


class OrganizationNotFoundError(Exception):
    pass


class RoomNotFoundError(Exception):
    pass


class InvalidAudiencePolicyError(Exception):
    pass


class CreatePostUseCase:
    """Use case pour la création d'une publication."""

    def __init__(self, post_repo: PostRepositoryPort):
        self._post_repo = post_repo

    def execute(self, user_id: UUID, tenant_id: UUID, dto: PostCreateDTO) -> Post:
        # Construction de l'AudiencePolicy
        # Si scope est LOCAL, target_tenant_ids doit être [tenant_id]
        # Si EXTENDED ou SPONSORED, il faut que des target_tenant_ids soient fournis
        # Ici on ne les reçoit pas dans le DTO, on suppose que le service gère ça
        # Par simplicité, on crée une politique basée sur le scope.
        if dto.scope == AudienceScope.LOCAL:
            audience_policy = AudiencePolicy(scope=dto.scope, target_tenant_ids=[tenant_id])
        elif dto.scope in (AudienceScope.EXTENDED, AudienceScope.SPONSORED):
            # Pour l'instant, on considère que les cibles doivent être précisées ailleurs
            # On lève une erreur si aucune cible n'est fournie (non géré dans le DTO)
            # Pour la démonstration, on autorise avec target_tenant_ids vide, à affiner.
            audience_policy = AudiencePolicy(scope=dto.scope, target_tenant_ids=[])
        else:  # PUBLIC
            audience_policy = AudiencePolicy(scope=dto.scope, target_tenant_ids=[])

        post = Post(
            id=uuid4(),
            tenant_id=tenant_id,
            author_id=user_id,
            type=dto.post_type,
            content=dto.content,
            audience_policy=audience_policy,
            organization_id=dto.organization_id,
            media_urls=dto.media_urls,
            is_sponsored=(dto.scope == AudienceScope.SPONSORED),
            views_count=0,
            created_at=datetime.utcnow(),
        )

        return self._post_repo.save(post)


class GetCampusFeedUseCase:
    """Use case pour récupérer le fil d'actualité selon l'onglet."""

    def __init__(self, post_repo: PostRepositoryPort):
        self._post_repo = post_repo

    def execute(
        self, tenant_id: UUID, user_id: UUID, tab: str, limit: int = 20, offset: int = 0
    ) -> List[Post]:
        # Le repository gère le filtrage selon tab et l'isolation tenant.
        return self._post_repo.list_feed(tenant_id, tab, user_id, limit, offset)


class DeclareRoomStatusUseCase:
    """Use case pour déclarer le statut d'une salle."""

    def __init__(self, room_repo: RoomRepositoryPort):
        self._room_repo = room_repo

    def execute(self, tenant_id: UUID, user_id: UUID, dto: RoomDeclareDTO) -> Room:
        room = self._room_repo.get_by_id(dto.room_id)
        if not room:
            raise RoomNotFoundError("Room not found")
        if room.tenant_id != tenant_id:
            raise RoomNotFoundError("Room does not belong to this tenant")

        # Mise à jour du statut
        room.status = dto.status

        # Si la salle est déclarée libre, on fixe une expiration
        if dto.status == RoomStatus.FREE:
            room.expires_at = datetime.utcnow() + timedelta(minutes=dto.validity_minutes)
        else:
            room.expires_at = None  # ou on garde l'ancienne expiration ?

        return self._room_repo.save(room)


class CreateOrganizationUseCase:
    """Use case pour créer une organisation (soumise à validation)."""

    def __init__(self, org_repo: OrganizationRepositoryPort):
        self._org_repo = org_repo

    def execute(self, tenant_id: UUID, owner_user_id: UUID, dto: OrganizationCreateDTO) -> Organization:
        # Création de l'organisation avec is_verified=False par défaut
        org = Organization(
            id=uuid4(),
            tenant_id=tenant_id,
            name=dto.name,
            slug=slugify(dto.name),  # fonction utilitaire à définir
            description=dto.description,
            type=dto.type,
            logo_url=dto.logo_url,
            is_verified=False,
            owner_user_id=owner_user_id,
        )
        return self._org_repo.save(org)


def slugify(name: str) -> str:
    """Convertit un nom en slug simple."""
    # Implémentation basique
    return name.lower().replace(" ", "-")


def uuid4() -> UUID:
    import uuid
    return uuid.uuid4()