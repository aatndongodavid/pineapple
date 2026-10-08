# backend/src/notification_context/domain/services/audience_resolver.py

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from identity_context.infrastructure.persistence.models import MembershipModel, UserModel
from identity_context.domain.value_objects import MembershipStatus


class AudienceResolver:
    """
    Résout la liste des identifiants d'utilisateurs destinataires
    en fonction du type d'audience d'un événement métier.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve_tenant_users(self, tenant_id: uuid.UUID) -> List[uuid.UUID]:
        """Retourne tous les membres actifs de l'établissement."""
        stmt = select(MembershipModel.user_id).where(
            MembershipModel.tenant_id == tenant_id,
            MembershipModel.status == MembershipStatus.ACTIVE
        )
        res = await self.db.execute(stmt)
        return list(set(res.scalars().all()))

    async def resolve_class_group_members(self, tenant_id: uuid.UUID, class_group_id: uuid.UUID) -> List[uuid.UUID]:
        """Retourne les membres inscrits dans un groupe-classe."""
        stmt = select(MembershipModel.user_id).where(
            MembershipModel.tenant_id == tenant_id,
            MembershipModel.class_group_id == class_group_id,
            MembershipModel.status == MembershipStatus.ACTIVE
        )
        res = await self.db.execute(stmt)
        return list(set(res.scalars().all()))

    async def resolve_single_user(self, user_id: uuid.UUID) -> List[uuid.UUID]:
        """Retourne une liste contenant uniquement l'utilisateur ciblé."""
        return [user_id]
