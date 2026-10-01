import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from community_context.application.dtos import (
    OrganizationCreateDTO,
    PostCreateDTO,
    PostResponseDTO,
    RoomDeclareDTO,
)
from community_context.application.use_cases import (
    CreateOrganizationUseCase,
    CreatePostUseCase,
    DeclareRoomStatusUseCase,
    GetCampusFeedUseCase,
    OrganizationNotFoundError,
    PostNotFoundError,
    RoomNotFoundError,
)
from community_context.domain.entities import Organization, Post, Room
from community_context.infrastructure.persistence.repositories import (
    PostgresOrganizationRepository,
    PostgresPostRepository,
    PostgresRoomRepository,
)
from shared_kernel.config import settings
from shared_kernel.infrastructure.database import AsyncSessionLocal
from shared_kernel.infrastructure.tenant_middleware import get_current_tenant_id

# ---------------------------------------------------------------------------
# Sécurité & dépendances transverses
# ---------------------------------------------------------------------------
security = HTTPBearer()


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return AsyncSessionLocal


async def get_post_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresPostRepository:
    return PostgresPostRepository(session_factory)


async def get_org_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresOrganizationRepository:
    return PostgresOrganizationRepository(session_factory)


async def get_room_repo(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> PostgresRoomRepository:
    return PostgresRoomRepository(session_factory)


from shared_kernel.infrastructure.auth import get_current_user, require_role


# ---------------------------------------------------------------------------
# Router principal
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/community", tags=["Campus Feed & Community"])


@router.get("/feed", response_model=List[PostResponseDTO])
async def get_feed(
    tab: str = Query("mon_etablissement", description="Onglet du fil"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    post_repo: PostgresPostRepository = Depends(get_post_repo),
):
    """
    Consulter le fil d'actualité du campus.
    Onglets supportés : mon_etablissement, pour_toi, communautes, marketplace.
    """
    use_case = GetCampusFeedUseCase(post_repo)
    posts = await use_case.execute(
        tenant_id=tenant_id,
        user_id=current_user["user_id"],
        tab=tab,
        limit=limit,
        offset=offset,
    )
    return [
        PostResponseDTO(
            id=post.id,
            tenant_id=post.tenant_id,
            author_id=post.author_id,
            organization_id=post.organization_id,
            content=post.content,
            post_type=post.type,
            media_urls=post.media_urls,
            scope=post.audience_policy.scope,
            is_sponsored=post.is_sponsored,
            views_count=post.views_count,
            created_at=post.created_at,
        )
        for post in posts
    ]


@router.post("/posts", response_model=PostResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_post(
    dto: PostCreateDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    post_repo: PostgresPostRepository = Depends(get_post_repo),
):
    """
    Créer une publication sur le fil avec filtrage de modération préventive.
    """
    from trust_safety_context.domain.content_moderation import ContentModerationService

    is_flagged, reason = ContentModerationService.inspect_text(dto.content)
    if is_flagged:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Publication mise en attente de modération préventive : {reason}",
        )

    use_case = CreatePostUseCase(post_repo)
    try:
        post = await use_case.execute(
            user_id=current_user["user_id"],
            tenant_id=tenant_id,
            dto=dto,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PostResponseDTO(
        id=post.id,
        tenant_id=post.tenant_id,
        author_id=post.author_id,
        organization_id=post.organization_id,
        content=post.content,
        post_type=post.type,
        media_urls=post.media_urls,
        scope=post.audience_policy.scope,
        is_sponsored=post.is_sponsored,
        views_count=post.views_count,
        created_at=post.created_at,
    )


@router.get("/organizations", response_model=List[dict])
async def list_organizations(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    org_repo: PostgresOrganizationRepository = Depends(get_org_repo),
):
    """
    Lister les clubs et associations de l'établissement.
    """
    orgs = await org_repo.list_by_tenant(tenant_id)
    return [
        {
            "id": org.id,
            "tenant_id": org.tenant_id,
            "name": org.name,
            "slug": org.slug,
            "description": org.description,
            "type": org.type.value,
            "logo_url": org.logo_url,
            "is_verified": org.is_verified,
            "owner_user_id": org.owner_user_id,
        }
        for org in orgs
    ]


@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def create_organization(
    dto: OrganizationCreateDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    org_repo: PostgresOrganizationRepository = Depends(get_org_repo),
):
    """
    Soumettre une création de club/association.
    """
    use_case = CreateOrganizationUseCase(org_repo)
    org = await use_case.execute(
        tenant_id=tenant_id,
        owner_user_id=current_user["user_id"],
        dto=dto,
    )
    return {
        "id": org.id,
        "tenant_id": org.tenant_id,
        "name": org.name,
        "slug": org.slug,
        "description": org.description,
        "type": org.type.value,
        "logo_url": org.logo_url,
        "is_verified": org.is_verified,
        "owner_user_id": org.owner_user_id,
    }


@router.patch("/organizations/{organization_id}/verify", response_model=dict)
async def verify_organization(
    organization_id: uuid.UUID,
    is_verified: bool = Query(True),
    admin: dict = Depends(require_role("ADMIN")),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    org_repo: PostgresOrganizationRepository = Depends(get_org_repo),
):
    """
    Valider ou rejeter un club/mouvement étudiant (réservé aux administrateurs).
    """
    org = await org_repo.get_by_id(organization_id, tenant_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    org.is_verified = is_verified
    await org_repo.save(org)
    
    return {
        "message": f"Organization {'verified' if is_verified else 'unverified'} successfully",
        "id": str(org.id),
        "is_verified": org.is_verified,
    }


@router.get("/rooms", response_model=List[dict])
async def list_rooms(
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    room_repo: PostgresRoomRepository = Depends(get_room_repo),
):
    """
    Obtenir la liste des salles et leur statut en temps réel.
    """
    rooms = await room_repo.list_rooms(tenant_id)
    return [
        {
            "id": room.id,
            "tenant_id": room.tenant_id,
            "name": room.name,
            "building": room.building,
            "status": room.status.value,
            "declared_by_user_id": room.declared_by_user_id,
            "expires_at": room.expires_at.isoformat() if room.expires_at else None,
        }
        for room in rooms
    ]


@router.post("/rooms/declare", response_model=dict)
async def declare_room(
    dto: RoomDeclareDTO,
    current_user: dict = Depends(get_current_user),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    room_repo: PostgresRoomRepository = Depends(get_room_repo),
):
    """
    Déclarer l'occupation ou la libération d'une salle.
    
    Portée d'accès (Option A) : Accessible à tout utilisateur authentifié disposant
    d'un statut actif ('ACTIVE').
    """
    use_case = DeclareRoomStatusUseCase(room_repo)
    try:
        room = await use_case.execute(
            tenant_id=tenant_id,
            user_id=current_user["user_id"],
            dto=dto,
        )
    except RoomNotFoundError:
        raise HTTPException(status_code=404, detail="Room not found")

    return {
        "id": room.id,
        "tenant_id": room.tenant_id,
        "name": room.name,
        "building": room.building,
        "status": room.status.value,
        "declared_by_user_id": room.declared_by_user_id,
        "expires_at": room.expires_at.isoformat() if room.expires_at else None,
    }