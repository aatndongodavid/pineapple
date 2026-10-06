import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set

from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared_kernel.config import settings
from shared_kernel.infrastructure.database import get_db_session

security_scheme = HTTPBearer(auto_error=False)

# Codes de permissions
ALL_PERMISSIONS = {
    # Public & Visiteur
    "feed.view_ads",
    "enrollment.claim",
    "enrollment.activate",
    "profile.manage",
    # Membre École (STUDENT)
    "feed.view_school",
    "feed.post",
    "room.view",
    "room.flag",
    "class.view",
    "academy.read",
    "market.use",
    "ride.use",
    "opportunities.use",
    "democracy.vote",
    "messaging.use",
    # Délégué (DELEGATE)
    "room.declare_status",
    "class.announce",
    "class.poll.create",
    "class.poll.vote",
    "class.poll.close",
    "class.incident.report",
    "class.event.manage",
    # Enseignant (TEACHER)
    "academy.publish",
    # Scolarité / Staff (STAFF)
    "admin.roster.manage",
    "admin.invitation.manage",
    "admin.membership.review",
    "admin.class.manage",
    "admin.room.manage",
    # Admin Établissement (TENANT_ADMIN)
    "admin.delegate.manage",
    "admin.settings.manage",
    "admin.subscription.view",
    "admin.audit.view",
    "democracy.manage",
    "moderation.review",
    # Super Admin Plateforme (PLATFORM_SUPER_ADMIN)
    "platform.tenant.manage",
}

ROLE_PERMISSIONS_MAP: Dict[str, Set[str]] = {
    "VISITOR": {
        "feed.view_ads",
        "enrollment.claim",
        "enrollment.activate",
        "profile.manage",
    },
    "STUDENT": {
        "feed.view_ads",
        "enrollment.claim",
        "enrollment.activate",
        "profile.manage",
        "feed.view_school",
        "feed.post",
        "room.view",
        "room.flag",
        "class.view",
        "academy.read",
        "market.use",
        "ride.use",
        "opportunities.use",
        "democracy.vote",
        "messaging.use",
        "class.poll.vote",
    },
    "DELEGATE": {
        "feed.view_ads",
        "enrollment.claim",
        "enrollment.activate",
        "profile.manage",
        "feed.view_school",
        "feed.post",
        "room.view",
        "room.flag",
        "class.view",
        "academy.read",
        "market.use",
        "ride.use",
        "opportunities.use",
        "democracy.vote",
        "messaging.use",
        "class.poll.vote",
        "room.declare_status",
        "class.announce",
        "class.poll.create",
        "class.poll.close",
        "class.incident.report",
        "class.event.manage",
    },
    "TEACHER": {
        "feed.view_ads",
        "enrollment.claim",
        "enrollment.activate",
        "profile.manage",
        "feed.view_school",
        "feed.post",
        "room.view",
        "room.flag",
        "class.view",
        "academy.read",
        "market.use",
        "ride.use",
        "opportunities.use",
        "democracy.vote",
        "messaging.use",
        "academy.publish",
    },
    "STAFF": {
        "feed.view_ads",
        "enrollment.claim",
        "enrollment.activate",
        "profile.manage",
        "feed.view_school",
        "feed.post",
        "room.view",
        "room.flag",
        "class.view",
        "academy.read",
        "market.use",
        "ride.use",
        "opportunities.use",
        "democracy.vote",
        "messaging.use",
        "admin.roster.manage",
        "admin.invitation.manage",
        "admin.membership.review",
        "admin.class.manage",
        "admin.room.manage",
    },
    "TENANT_ADMIN": {
        "feed.view_ads",
        "enrollment.claim",
        "enrollment.activate",
        "profile.manage",
        "feed.view_school",
        "feed.post",
        "room.view",
        "room.flag",
        "class.view",
        "academy.read",
        "market.use",
        "ride.use",
        "opportunities.use",
        "democracy.vote",
        "messaging.use",
        "admin.roster.manage",
        "admin.invitation.manage",
        "admin.membership.review",
        "admin.class.manage",
        "admin.room.manage",
        "admin.delegate.manage",
        "admin.settings.manage",
        "admin.subscription.view",
        "admin.audit.view",
        "democracy.manage",
        "moderation.review",
        "academy.publish",
    },
    "PLATFORM_SUPER_ADMIN": ALL_PERMISSIONS,
}


def create_jwt_token(
    user_id: uuid.UUID,
    tenant_id: Optional[uuid.UUID] = None,
    membership_id: Optional[uuid.UUID] = None,
    role: str = "VISITOR",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Génère un JWT contenant sub, tid, mid, role, jti, exp."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "tid": str(tenant_id) if tenant_id else None,
        "mid": str(membership_id) if membership_id else None,
        "role": role,
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


create_access_token = create_jwt_token


def decode_jwt_token(token: str) -> dict:
    """Décode et valide un JWT."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthenticatedUserContext:
    def __init__(
        self,
        user_id: uuid.UUID,
        user_type: str,
        email: str,
        first_name: str,
        last_name: str,
        tenant_id: Optional[uuid.UUID],
        membership_id: Optional[uuid.UUID],
        class_group_id: Optional[uuid.UUID],
        role: str,
        permissions: Set[str],
        delegate_of: List[uuid.UUID],
        subscription_status: str = "ACTIVE",
    ):
        self.user_id = user_id
        self.user_type = user_type
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.tenant_id = tenant_id
        self.membership_id = membership_id
        self.class_group_id = class_group_id
        self.role = role
        self.permissions = permissions
        self.delegate_of = delegate_of
        self.subscription_status = subscription_status

    def can(self, permission: str) -> bool:
        return permission in self.permissions or "platform.tenant.manage" in self.permissions


async def get_user_context(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db_session),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
) -> AuthenticatedUserContext:
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise",
        )

    payload = decode_jwt_token(auth.credentials)
    user_id = uuid.UUID(payload["sub"])
    jwt_tid = payload.get("tid")

    # Décision D4 : si X-Tenant-ID est présent et != tid dans JWT, refuser avec 403
    if x_tenant_id and jwt_tid and x_tenant_id != jwt_tid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Header X-Tenant-ID non autorisé pour ce jeton",
        )

    # Récupérer l'utilisateur en base
    from identity_context.infrastructure.persistence.models import (
        ClassDelegateModel,
        MembershipModel,
        TenantSubscriptionModel,
        UserModel,
    )

    user = await db.get(UserModel, user_id)
    if not user or user.account_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte inexistant ou inactif",
        )

    if user.user_type == "PLATFORM_ADMIN":
        return AuthenticatedUserContext(
            user_id=user.id,
            user_type=user.user_type,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            tenant_id=None,
            membership_id=None,
            class_group_id=None,
            role="PLATFORM_SUPER_ADMIN",
            permissions=ALL_PERMISSIONS,
            delegate_of=[],
            subscription_status="ACTIVE",
        )

    # Récupérer l'appartenance active (Membership)
    m_stmt = select(MembershipModel).where(
        MembershipModel.user_id == user.id,
        MembershipModel.status.in_(["ACTIVE", "PENDING"]),
    )
    m_res = await db.execute(m_stmt)
    membership = m_res.scalars().first()

    if not membership or membership.status == "PENDING":
        # Utilisateur Visiteur sans membership actif
        return AuthenticatedUserContext(
            user_id=user.id,
            user_type=user.user_type,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            tenant_id=None,
            membership_id=None,
            class_group_id=None,
            role="VISITOR",
            permissions=ROLE_PERMISSIONS_MAP["VISITOR"],
            delegate_of=[],
            subscription_status="NONE",
        )

    tenant_id = membership.tenant_id
    class_group_id = membership.class_group_id
    role = membership.role
    permissions = set(ROLE_PERMISSIONS_MAP.get(role, ROLE_PERMISSIONS_MAP["STUDENT"]))

    # Vérifier les délégations actives
    del_stmt = select(ClassDelegateModel).where(
        ClassDelegateModel.user_id == user.id,
        ClassDelegateModel.tenant_id == tenant_id,
        ClassDelegateModel.revoked_at.is_(None),
    )
    del_res = await db.execute(del_stmt)
    delegates = del_res.scalars().all()
    delegate_of_classes = [d.class_group_id for d in delegates]

    if delegate_of_classes:
        permissions.update(ROLE_PERMISSIONS_MAP["DELEGATE"])

    # Vérifier le statut de l'abonnement du tenant
    sub_stmt = select(TenantSubscriptionModel).where(
        TenantSubscriptionModel.tenant_id == tenant_id
    )
    sub_res = await db.execute(sub_stmt)
    subscription = sub_res.scalars().first()
    sub_status = subscription.status if subscription else "ACTIVE"

    return AuthenticatedUserContext(
        user_id=user.id,
        user_type=user.user_type,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        tenant_id=tenant_id,
        membership_id=membership.id,
        class_group_id=class_group_id,
        role=role,
        permissions=permissions,
        delegate_of=delegate_of_classes,
        subscription_status=sub_status,
    )


def require_permission(permission_code: str):
    """Dépendance FastAPI pour exiger une permission spécifique."""

    async def _dependency(ctx: AuthenticatedUserContext = Depends(get_user_context)):
        if not ctx.can(permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "PERMISSION_DENIED", "message": f"Permission requise : {permission_code}"},
            )
        # Règle abonnement inactif : membres passent en lecture seule si création
        if ctx.subscription_status in ["EXPIRED", "SUSPENDED"] and permission_code not in [
            "room.view", "feed.view_school", "academy.read", "admin.subscription.view", "profile.manage"
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "SUBSCRIPTION_INACTIVE", "message": "Abonnement de l'établissement inactif (lecture seule)"},
            )
        return ctx

    return _dependency


def require_membership():
    """Dépendance FastAPI exigeant un membership actif (non Visiteur)."""

    async def _dependency(ctx: AuthenticatedUserContext = Depends(get_user_context)):
        if ctx.role == "VISITOR" or not ctx.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "SCHOOL_MEMBERSHIP_REQUIRED", "message": "Appartenance à un établissement requise"},
            )
        return ctx

    return _dependency


def require_class_scope(param_name: str = "class_group_id"):
    """Dépendance vérifiant que le délégué agit bien sur sa propre classe (S9)."""

    async def _dependency(request: Request, ctx: AuthenticatedUserContext = Depends(get_user_context)):
        target_class_id_str = request.path_params.get(param_name) or request.query_params.get(param_name)
        if target_class_id_str and ctx.role != "PLATFORM_SUPER_ADMIN" and ctx.role != "TENANT_ADMIN":
            target_class_id = uuid.UUID(target_class_id_str)
            if target_class_id not in ctx.delegate_of and target_class_id != ctx.class_group_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "PERMISSION_DENIED", "message": "Action limitée à votre propre classe"},
                )
        return ctx

    return _dependency
