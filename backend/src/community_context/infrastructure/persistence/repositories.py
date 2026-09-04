from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from community_context.domain.entities import Organization, Post, Room
from community_context.domain.ports import (
    OrganizationRepositoryPort,
    PostRepositoryPort,
    RoomRepositoryPort,
)
from community_context.domain.value_objects import (
    AudiencePolicy,
    AudienceScope,
    OrganizationType,
    PostType,
    RoomStatus,
)
from community_context.infrastructure.persistence.models import (
    OrganizationModel,
    PostModel,
    RoomModel,
)


class PostgresPostRepository(PostRepositoryPort):
    """Implémentation PostgreSQL du port PostRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_entity(model: PostModel) -> Post:
        """Convertit un modèle ORM en entité Post."""
        return Post(
            id=model.id,
            tenant_id=model.tenant_id,
            author_id=model.author_id,
            type=model.type,
            content=model.content,
            audience_policy=AudiencePolicy(
                scope=model.scope,
                target_tenant_ids=[],  # Non stocké dans le modèle actuel
            ),
            organization_id=model.organization_id,
            media_urls=model.media_urls,
            is_sponsored=model.is_sponsored,
            views_count=model.views_count,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_model(post: Post) -> PostModel:
        """Convertit une entité Post en modèle ORM."""
        return PostModel(
            id=post.id,
            tenant_id=post.tenant_id,
            author_id=post.author_id,
            type=post.type,
            content=post.content,
            media_urls=post.media_urls,
            scope=post.audience_policy.scope,
            is_sponsored=post.is_sponsored,
            views_count=post.views_count,
            organization_id=post.organization_id,
            created_at=post.created_at,
        )

    async def save(self, post: Post) -> Post:
        async with self._session_factory() as session:
            model = self._to_model(post)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return post

    async def get_by_id(self, post_id: UUID) -> Optional[Post]:
        async with self._session_factory() as session:
            stmt = select(PostModel).where(PostModel.id == post_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def list_feed(
        self,
        tenant_id: UUID,
        tab: str,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Post]:
        async with self._session_factory() as session:
            stmt = select(PostModel).where(PostModel.tenant_id == tenant_id)

            # Filtrage selon l'onglet demandé
            if tab == "mon_etablissement":
                # Publications organiques locales (scope LOCAL)
                stmt = stmt.where(PostModel.scope == AudienceScope.LOCAL)
            elif tab == "pour_toi":
                # Pour l'instant, on retourne toutes les publications locales non sponsorisées
                stmt = stmt.where(PostModel.is_sponsored == False)
            elif tab == "communautes":
                # Publications provenant d'organisations
                stmt = stmt.where(PostModel.organization_id.isnot(None))
            elif tab == "marketplace":
                # Le fil marketplace n'est pas géré ici ; retourner vide
                return []
            # Les autres onglets (academy, opportunities) ne sont pas gérés ici

            stmt = stmt.order_by(PostModel.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]


class PostgresOrganizationRepository(OrganizationRepositoryPort):
    """Implémentation PostgreSQL du port OrganizationRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_entity(model: OrganizationModel) -> Organization:
        return Organization(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            slug=model.slug,
            description=model.description,
            type=model.type,
            logo_url=model.logo_url,
            is_verified=model.is_verified,
            owner_user_id=model.owner_user_id,
        )

    @staticmethod
    def _to_model(org: Organization) -> OrganizationModel:
        return OrganizationModel(
            id=org.id,
            tenant_id=org.tenant_id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            type=org.type,
            logo_url=org.logo_url,
            is_verified=org.is_verified,
            owner_user_id=org.owner_user_id,
        )

    async def save(self, org: Organization) -> Organization:
        async with self._session_factory() as session:
            model = self._to_model(org)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return org

    async def get_by_id(self, org_id: UUID, tenant_id: UUID) -> Optional[Organization]:
        async with self._session_factory() as session:
            stmt = select(OrganizationModel).where(
                OrganizationModel.id == org_id,
                OrganizationModel.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def list_by_tenant(self, tenant_id: UUID) -> List[Organization]:
        async with self._session_factory() as session:
            stmt = select(OrganizationModel).where(OrganizationModel.tenant_id == tenant_id)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]


class PostgresRoomRepository(RoomRepositoryPort):
    """Implémentation PostgreSQL du port RoomRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @staticmethod
    def _to_entity(model: RoomModel) -> Room:
        return Room(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            building=model.building,
            status=model.status,
            declared_by_user_id=model.declared_by_user_id,
            expires_at=model.expires_at,
        )

    @staticmethod
    def _to_model(room: Room) -> RoomModel:
        return RoomModel(
            id=room.id,
            tenant_id=room.tenant_id,
            name=room.name,
            building=room.building,
            status=room.status,
            declared_by_user_id=room.declared_by_user_id,
            expires_at=room.expires_at,
        )

    async def save(self, room: Room) -> Room:
        async with self._session_factory() as session:
            model = self._to_model(room)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return room

    async def list_rooms(self, tenant_id: UUID) -> List[Room]:
        async with self._session_factory() as session:
            stmt = select(RoomModel).where(RoomModel.tenant_id == tenant_id)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_entity(m) for m in models]

    async def get_by_id(self, room_id: UUID) -> Optional[Room]:
        async with self._session_factory() as session:
            stmt = select(RoomModel).where(RoomModel.id == room_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None