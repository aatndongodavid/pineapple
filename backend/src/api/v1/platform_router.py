import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from identity_context.infrastructure.persistence.models import (
    MembershipModel,
    RosterEntryModel,
    TenantModel,
    TenantSubscriptionModel,
    UserModel,
)
from shared_kernel.infrastructure.audit_log import log_audit_event
from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.email_gateway import email_gateway
from shared_kernel.infrastructure.security import (
    AuthenticatedUserContext,
    require_permission,
)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

router = APIRouter(prefix="/platform", tags=["Platform Super Admin"])


class TenantCreateDTO(BaseModel):
    name: str
    code: str
    admin_email: str
    admin_first_name: str
    admin_last_name: str
    country: str = "Cameroun"
    seats_limit: int = 1000
    plan: str = "STANDARD"


class TenantSubscriptionUpdateDTO(BaseModel):
    status: str  # ACTIVE, TRIAL, PAST_DUE, SUSPENDED, EXPIRED
    seats_limit: Optional[int] = None
    extend_days: Optional[int] = None


@router.get("/tenants")
async def list_tenants(
    ctx: AuthenticatedUserContext = Depends(require_permission("platform.tenant.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(TenantModel).order_by(TenantModel.created_at.desc())
    res = await db.execute(stmt)
    tenants = res.scalars().all()

    output = []
    for t in tenants:
        sub_stmt = select(TenantSubscriptionModel).where(TenantSubscriptionModel.tenant_id == t.id)
        sub = (await db.execute(sub_stmt)).scalars().first()

        output.append({
            "id": str(t.id),
            "name": t.name,
            "code": t.code,
            "country": t.country,
            "is_active": t.is_active,
            "subscription": {
                "plan": sub.plan if sub else "STANDARD",
                "status": sub.status if sub else "ACTIVE",
                "seats_limit": sub.seats_limit if sub else 1000,
                "ends_at": sub.ends_at.isoformat() if sub and sub.ends_at else None,
            },
        })
    return output


@router.post("/tenants", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    dto: TenantCreateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("platform.tenant.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    """Création d'un établissement par l'équipe Pineapple + invitation du 1er TENANT_ADMIN."""
    now = datetime.now(timezone.utc)
    tenant_id = uuid.uuid4()

    tenant = TenantModel(
        id=tenant_id,
        name=dto.name.strip(),
        code=dto.code.strip().upper(),
        country=dto.country,
        enrollment_mode="BOTH",
        auto_approve_claims=True,
        current_academic_year="2026-2027",
        is_active=True,
        created_at=now,
    )
    db.add(tenant)

    sub = TenantSubscriptionModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        plan=dto.plan,
        status="ACTIVE",
        seats_limit=dto.seats_limit,
        starts_at=now,
        ends_at=now + timedelta(days=365),
    )
    db.add(sub)

    # Créer le compte utilisateur Admin de l'établissement
    admin_user_id = uuid.uuid4()
    temp_pwd = "".join(secrets.choice(string.ascii_letters + string.digits + "!@#$") for _ in range(12))

    admin_user = UserModel(
        id=admin_user_id,
        email=dto.admin_email.lower().strip(),
        hashed_password=pwd_context.hash(temp_pwd),
        first_name=dto.admin_first_name,
        last_name=dto.admin_last_name,
        account_status="ACTIVE",
        must_change_password=True,
    )
    db.add(admin_user)

    membership = MembershipModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=admin_user_id,
        role="TENANT_ADMIN",
        status="ACTIVE",
        joined_via="ADMIN",
        joined_at=now,
        academic_year="2026-2027",
    )
    db.add(membership)

    email_html = f"""
    <h2>Bienvenue sur Pineapple OS — Administration de {tenant.name}</h2>
    <p>Bonjour {dto.admin_first_name},</p>
    <p>Votre établissement a été configuré avec succès sur Pineapple OS.</p>
    <p><b>Identifiant :</b> {dto.admin_email}<br>
    <b>Mot de passe temporaire :</b> <code>{temp_pwd}</code></p>
    <p>Connectez-vous pour accéder au tableau de bord administrateur : <a href="http://localhost:3000/login">Connexion Admin</a></p>
    """
    await email_gateway.send_email(dto.admin_email, f"Accès Administrateur — {tenant.name}", email_html)

    await log_audit_event(db, "PLATFORM_TENANT_CREATE", "tenant", None, ctx.user_id, str(tenant_id), {"name": tenant.name, "code": tenant.code})
    await db.commit()

    return {
        "tenant_id": str(tenant_id),
        "admin_user_id": str(admin_user_id),
        "admin_temp_password": temp_pwd,
    }


@router.patch("/tenants/{tenant_id}/subscription")
async def update_tenant_subscription(
    tenant_id: str,
    dto: TenantSubscriptionUpdateDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("platform.tenant.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    tid = uuid.UUID(tenant_id)
    sub = (await db.execute(select(TenantSubscriptionModel).where(TenantSubscriptionModel.tenant_id == tid))).scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="Abonnement non trouvé")

    sub.status = dto.status
    if dto.seats_limit is not None:
        sub.seats_limit = dto.seats_limit
    if dto.extend_days:
        sub.ends_at += timedelta(days=dto.extend_days)

    await log_audit_event(db, "PLATFORM_SUBSCRIPTION_UPDATE", "tenant_subscription", tid, ctx.user_id, str(sub.id), {"status": dto.status})
    await db.commit()
    return {"status": sub.status, "ends_at": sub.ends_at.isoformat()}
