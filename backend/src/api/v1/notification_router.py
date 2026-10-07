# backend/src/api/v1/notification_router.py

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.security import (
    AuthenticatedUserContext,
    require_membership,
    require_permission,
)
from notification_context.domain.value_objects import (
    NotificationCategory, NotificationChannel, DeliveryStatus
)
from notification_context.infrastructure.persistence.models import (
    NotificationModel, NotificationPreferenceModel, QuietHoursModel,
    PushSubscriptionModel, ChannelQuotaModel, NotificationDeliveryModel
)
from notification_context.infrastructure.adapters.email_gateway import EmailGatewayAdapter
from notification_context.domain.services.broadcast_service import BroadcastService
from identity_context.domain.value_objects import MembershipRole

router = APIRouter(prefix="/notifications", tags=["Notifications Multicanal"])


# --- DTOs ---
class NotificationDTO(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    category: str
    title: str
    body: str
    deep_link: Optional[str]
    is_read: bool
    read_at: Optional[str]
    created_at: str


class UnreadCountDTO(BaseModel):
    unread_count: int


class PreferenceUpdateDTO(BaseModel):
    category: str
    channel: str
    is_enabled: bool


class QuietHoursUpdateDTO(BaseModel):
    start_hour: int = Field(..., ge=0, le=23)
    end_hour: int = Field(..., ge=0, le=23)
    is_enabled: bool = True


class WebPushSubscribeDTO(BaseModel):
    endpoint: str
    p256dh_key: str
    auth_key: str
    user_agent: Optional[str] = None


class BroadcastRequestDTO(BaseModel):
    target: str = Field(..., description="CLASS_GROUP or TENANT_ALL")
    class_group_id: Optional[str] = None
    title: str
    body: str
    category: str = "IMPORTANT"
    criticality: str = "IMPORTANT"
    deep_link: Optional[str] = None
    channels: Optional[List[str]] = None


class AdminAnalyticsDTO(BaseModel):
    total_notifications: int
    delivered_count: int
    failed_count: int
    sms_quota_used: int
    sms_quota_limit: int
    delivery_rate_percent: float


# --- Endpoints ---

@router.get("", response_model=List[NotificationDTO])
async def list_user_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    auth: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Récupère les notifications In-App paginées pour l'utilisateur courant.
    """
    offset = (page - 1) * page_size
    query = select(NotificationModel).where(
        NotificationModel.user_id == auth.user_id,
        NotificationModel.tenant_id == auth.tenant_id,
    )
    if category:
        query = query.where(NotificationModel.category == category)
    if unread_only:
        query = query.where(NotificationModel.is_read == False)

    query = query.order_by(NotificationModel.created_at.desc()).offset(offset).limit(page_size)
    res = await db.execute(query)
    notifs = res.scalars().all()

    return [
        NotificationDTO(
            id=str(n.id),
            tenant_id=str(n.tenant_id),
            user_id=str(n.user_id),
            category=n.category,
            title=n.title,
            body=n.body,
            deep_link=n.deep_link,
            is_read=n.is_read,
            read_at=n.read_at.isoformat() if n.read_at else None,
            created_at=n.created_at.isoformat(),
        )
        for n in notifs
    ]


@router.get("/unread-count", response_model=UnreadCountDTO)
async def get_unread_count(
    auth: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Compte rapide des notifications non lues (pour le badge dans la navbar).
    """
    stmt = select(func.count(NotificationModel.id)).where(
        NotificationModel.user_id == auth.user_id,
        NotificationModel.tenant_id == auth.tenant_id,
        NotificationModel.is_read == False,
    )
    res = await db.execute(stmt)
    count = res.scalar_one() or 0
    return UnreadCountDTO(unread_count=count)


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: uuid.UUID,
    auth: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Marque une notification comme lue.
    """
    stmt = select(NotificationModel).where(
        NotificationModel.id == notification_id,
        NotificationModel.user_id == auth.user_id,
        NotificationModel.tenant_id == auth.tenant_id,
    )
    res = await db.execute(stmt)
    notif = res.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification introuvable")

    if not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        await db.commit()

    return {"status": "success", "message": "Notification marquée comme lue"}


@router.post("/read-all")
async def mark_all_read(
    auth: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Marque toutes les notifications de l'utilisateur comme lues.
    """
    stmt = update(NotificationModel).where(
        NotificationModel.user_id == auth.user_id,
        NotificationModel.tenant_id == auth.tenant_id,
        NotificationModel.is_read == False,
    ).values(
        is_read=True,
        read_at=datetime.now(timezone.utc),
    )
    await db.execute(stmt)
    await db.commit()
    return {"status": "success", "message": "Toutes les notifications ont été marquées comme lues"}


@router.get("/preferences")
async def get_preferences(
    auth: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Récupère la matrice des préférences et la configuration des heures calmes.
    """
    pref_stmt = select(NotificationPreferenceModel).where(
        NotificationPreferenceModel.user_id == auth.user_id,
        NotificationPreferenceModel.tenant_id == auth.tenant_id,
    )
    pref_res = await db.execute(pref_stmt)
    prefs = pref_res.scalars().all()

    qh_stmt = select(QuietHoursModel).where(QuietHoursModel.user_id == auth.user_id)
    qh_res = await db.execute(qh_stmt)
    qh = qh_res.scalars().first()

    return {
        "preferences": [
            {
                "category": p.category,
                "channel": p.channel,
                "is_enabled": p.is_enabled,
            }
            for p in prefs
        ],
        "quiet_hours": {
            "start_hour": qh.start_hour if qh else 21,
            "end_hour": qh.end_hour if qh else 6,
            "is_enabled": qh.is_enabled if qh else False,
        } if qh else None
    }


@router.put("/preferences")
async def update_preference(
    dto: PreferenceUpdateDTO,
    auth: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Met à jour la préférence pour un couple (catégorie x canal).
    """
    pref_stmt = select(NotificationPreferenceModel).where(
        NotificationPreferenceModel.user_id == auth.user_id,
        NotificationPreferenceModel.tenant_id == auth.tenant_id,
        NotificationPreferenceModel.category == dto.category,
        NotificationPreferenceModel.channel == dto.channel,
    )
    pref_res = await db.execute(pref_stmt)
    pref = pref_res.scalars().first()

    if pref:
        pref.is_enabled = dto.is_enabled
        pref.updated_at = datetime.now(timezone.utc)
    else:
        pref = NotificationPreferenceModel(
            id=uuid.uuid4(),
            user_id=auth.user_id,
            tenant_id=auth.tenant_id,
            category=dto.category,
            channel=dto.channel,
            is_enabled=dto.is_enabled,
        )
        db.add(pref)

    await db.commit()
    return {"status": "success", "message": "Préférence mise à jour"}


@router.put("/quiet-hours")
async def update_quiet_hours(
    dto: QuietHoursUpdateDTO,
    auth: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Configure les heures calmes pour l'utilisateur.
    """
    qh_stmt = select(QuietHoursModel).where(QuietHoursModel.user_id == auth.user_id)
    qh_res = await db.execute(qh_stmt)
    qh = qh_res.scalars().first()

    if qh:
        qh.tenant_id = auth.tenant_id
        qh.start_hour = dto.start_hour
        qh.end_hour = dto.end_hour
        qh.is_enabled = dto.is_enabled
        qh.updated_at = datetime.now(timezone.utc)
    else:
        qh = QuietHoursModel(
            id=uuid.uuid4(),
            user_id=auth.user_id,
            tenant_id=auth.tenant_id,
            start_hour=dto.start_hour,
            end_hour=dto.end_hour,
            is_enabled=dto.is_enabled,
        )
        db.add(qh)

    await db.commit()
    return {"status": "success", "message": "Heures calmes mises à jour"}


@router.post("/push/subscribe")
async def subscribe_web_push(
    dto: WebPushSubscribeDTO,
    auth_ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Enregistre un abonnement Web Push VAPID pour le navigateur courant.
    """
    existing_stmt = select(PushSubscriptionModel).where(
        PushSubscriptionModel.user_id == auth_ctx.user_id,
        PushSubscriptionModel.endpoint == dto.endpoint,
    )
    res = await db.execute(existing_stmt)
    sub = res.scalars().first()

    if not sub:
        sub = PushSubscriptionModel(
            id=uuid.uuid4(),
            user_id=auth_ctx.user_id,
            tenant_id=auth_ctx.tenant_id,
            endpoint=dto.endpoint,
            p256dh=dto.p256dh_key,
            auth=dto.auth_key,
            user_agent=dto.user_agent,
        )
        db.add(sub)
        await db.commit()

    return {"status": "success", "message": "Abonnement Web Push enregistré"}


@router.post("/push/unsubscribe")
async def unsubscribe_web_push(
    endpoint: str = Query(...),
    auth_ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Supprime un abonnement Web Push.
    """
    stmt = select(PushSubscriptionModel).where(
        PushSubscriptionModel.user_id == auth_ctx.user_id,
        PushSubscriptionModel.endpoint == endpoint,
    )
    res = await db.execute(stmt)
    sub = res.scalars().first()
    if sub:
        await db.delete(sub)
        await db.commit()

    return {"status": "success", "message": "Abonnement Web Push supprimé"}


@router.post("/broadcast")
async def broadcast_announcement(
    dto: BroadcastRequestDTO,
    auth: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Diffusion d'annonce (Délégué -> Classe, Admin -> Établissement).
    """
    bcast_service = BroadcastService(db)
    cat = NotificationCategory(dto.category)
    crit = NotificationCategory(dto.criticality)
    parsed_channels = [NotificationChannel(ch) for ch in dto.channels] if dto.channels else None

    if dto.target == "CLASS_GROUP":
        if not dto.class_group_id:
            raise HTTPException(status_code=400, detail="class_group_id requis pour une diffusion de classe")
        
        success, count, ref_or_reason = await bcast_service.broadcast_to_class_group(
            tenant_id=auth.tenant_id,
            author_id=auth.user_id,
            class_group_id=uuid.UUID(dto.class_group_id),
            title=dto.title,
            body=dto.body,
            category=cat,
            criticality=crit,
            deep_link=dto.deep_link,
            channels=parsed_channels,
        )
        if not success:
            raise HTTPException(status_code=429, detail=f"Quota dépassé: {ref_or_reason}")

        await db.commit()
        return {"status": "success", "recipients_count": count, "broadcast_ref": ref_or_reason}

    elif dto.target == "TENANT_ALL":
        if auth.role not in [MembershipRole.TENANT_ADMIN]:
            raise HTTPException(status_code=403, detail="Permission refusée. Seul un administrateur peut diffuser à tout l'établissement.")

        success, count, ref_or_reason = await bcast_service.broadcast_to_tenant(
            tenant_id=auth.tenant_id,
            author_id=auth.user_id,
            title=dto.title,
            body=dto.body,
            category=cat,
            criticality=crit,
            deep_link=dto.deep_link,
            channels=parsed_channels,
        )
        await db.commit()
        return {"status": "success", "recipients_count": count, "broadcast_ref": ref_or_reason}

    else:
        raise HTTPException(status_code=400, detail="Cible de diffusion invalide (CLASS_GROUP ou TENANT_ALL)")


@router.get("/admin/analytics", response_model=AdminAnalyticsDTO)
async def get_admin_notification_analytics(
    auth: AuthenticatedUserContext = Depends(require_permission("tenant.manage")),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Statistiques et métriques de consommation pour l'administration.
    """
    # Total notifications
    tot_stmt = select(func.count(NotificationDeliveryModel.id)).where(
        NotificationDeliveryModel.tenant_id == auth.tenant_id
    )
    tot_res = await db.execute(tot_stmt)
    total_notifs = tot_res.scalar_one() or 0

    # Delivered count
    del_stmt = select(func.count(NotificationDeliveryModel.id)).where(
        NotificationDeliveryModel.tenant_id == auth.tenant_id,
        NotificationDeliveryModel.status == DeliveryStatus.DELIVERED.value,
    )
    del_res = await db.execute(del_stmt)
    delivered_count = del_res.scalar_one() or 0

    # Failed count
    fail_stmt = select(func.count(NotificationDeliveryModel.id)).where(
        NotificationDeliveryModel.tenant_id == auth.tenant_id,
        NotificationDeliveryModel.status == DeliveryStatus.FAILED.value,
    )
    fail_res = await db.execute(fail_stmt)
    failed_count = fail_res.scalar_one() or 0

    # SMS Quota usage
    sms_quota_stmt = select(ChannelQuotaModel).where(
        ChannelQuotaModel.tenant_id == auth.tenant_id,
        ChannelQuotaModel.channel == "SMS",
    )
    sms_res = await db.execute(sms_quota_stmt)
    sms_quota = sms_res.scalars().first()

    sms_quota_used = sms_quota.current_usage if sms_quota else 0
    sms_quota_limit = sms_quota.max_limit if sms_quota else 500

    rate = round((delivered_count / total_notifs * 100), 2) if total_notifs > 0 else 100.0

    return AdminAnalyticsDTO(
        total_notifications=total_notifications,
        delivered_count=delivered_count,
        failed_count=failed_count,
        sms_quota_used=sms_quota_used,
        sms_quota_limit=sms_quota_limit,
        delivery_rate_percent=rate,
    )


@router.get("/email/unsubscribe")
async def email_one_click_unsubscribe(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Désabonnement en 1-clic depuis un e-mail (RFC 8058).
    Aucune authentification requise (vérification par JWT signé).
    """
    payload = EmailGatewayAdapter.verify_unsubscribe_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Token de désabonnement invalide ou expiré")

    user_id = uuid.UUID(payload["sub"])
    tenant_id = uuid.UUID(payload["tid"])
    category = payload.get("cat", "IMPORTANT")

    # Désactiver le canal EMAIL pour cette catégorie
    pref_stmt = select(NotificationPreferenceModel).where(
        NotificationPreferenceModel.user_id == user_id,
        NotificationPreferenceModel.tenant_id == tenant_id,
        NotificationPreferenceModel.category == category,
        NotificationPreferenceModel.channel == "EMAIL",
    )
    res = await db.execute(pref_stmt)
    pref = res.scalars().first()

    if pref:
        pref.is_enabled = False
        pref.updated_at = datetime.now(timezone.utc)
    else:
        pref = NotificationPreferenceModel(
            id=uuid.uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            category=category,
            channel="EMAIL",
            is_enabled=False,
        )
        db.add(pref)

    await db.commit()

    return {
        "status": "success",
        "message": f"Vous avez été désabonné des e-mails pour la catégorie {category}.",
    }
