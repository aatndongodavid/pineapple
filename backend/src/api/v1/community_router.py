import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from community_context.domain.value_objects import RoomStatus
from community_context.infrastructure.persistence.models import (
    OrganizationModel,
    PostModel,
    RoomModel,
    RoomStatusDeclarationModel,
)
from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.security import (
    AuthenticatedUserContext,
    require_membership,
    require_permission,
)

router = APIRouter(prefix="/community", tags=["Campus Feed & Rooms"])


class RoomDeclareRequestDTO(BaseModel):
    status: str  # FREE, OCCUPIED, TO_CONFIRM
    note: Optional[str] = None
    duration_minutes: int = 120


class RoomFlagRequestDTO(BaseModel):
    reason: str = Field(..., description="Motif du signalement d'incohérence")


@router.get("/rooms")
async def list_rooms(
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Consulter l'état courant de toutes les salles de l'établissement en temps réel.
    """
    now = datetime.now(timezone.utc)
    stmt = select(RoomModel).where(RoomModel.tenant_id == ctx.tenant_id, RoomModel.is_active.is_(True)).order_by(RoomModel.name)
    res = await db.execute(stmt)
    rooms = res.scalars().all()

    output = []
    for r in rooms:
        # Vérification d'expiration automatique
        is_expired = r.expires_at and r.expires_at < now
        current_status = RoomStatus.FREE.value if is_expired else r.status.value

        output.append({
            "id": str(r.id),
            "name": r.name,
            "building": r.building,
            "capacity": r.capacity,
            "status": current_status,
            "declared_by_user_id": str(r.declared_by_user_id) if r.declared_by_user_id and not is_expired else None,
            "class_group_id": str(r.class_group_id) if r.class_group_id and not is_expired else None,
            "expires_at": r.expires_at.isoformat() if r.expires_at and not is_expired else None,
        })
    return output


@router.post("/rooms/{room_id}/status")
async def declare_room_status(
    room_id: str,
    dto: RoomDeclareRequestDTO,
    ctx: AuthenticatedUserContext = Depends(require_permission("room.declare_status")),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Déclarer l'état d'une salle. Réservé exclusivement aux Délégués de Classe actifs (S7).
    Les étudiants non-délégués reçoivent une réponse 403 Forbidden.
    """
    rid = uuid.UUID(room_id)
    room = await db.get(RoomModel, rid)
    if not room or room.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Salle non trouvée")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=dto.duration_minutes)

    try:
        new_status = RoomStatus(dto.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Statut de salle invalide (FREE, OCCUPIED, TO_CONFIRM)")

    room.status = new_status
    room.declared_by_user_id = ctx.user_id
    room.class_group_id = ctx.class_group_id
    room.expires_at = expires_at

    declaration = RoomStatusDeclarationModel(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        room_id=rid,
        class_group_id=ctx.class_group_id,
        declared_by_user_id=ctx.user_id,
        status=new_status,
        note=dto.note,
        declared_at=now,
        expires_at=expires_at,
    )
    db.add(declaration)
    await db.commit()

    return {
        "id": str(room.id),
        "name": room.name,
        "status": room.status.value,
        "declared_by_user_id": str(room.declared_by_user_id),
        "expires_at": room.expires_at.isoformat(),
    }


@router.post("/rooms/{room_id}/flag")
async def flag_room_inconsistency(
    room_id: str,
    dto: RoomFlagRequestDTO,
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Signaler une incohérence d'état de salle (« Cet état est faux »).
    Accessible à tous les membres étudiants.
    """
    rid = uuid.UUID(room_id)
    room = await db.get(RoomModel, rid)
    if not room or room.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Salle non trouvée")

    room.status = RoomStatus.TO_CONFIRM
    await db.commit()

    return {"status": "ok", "message": "Signalement enregistré. L'état est maintenant sous vérification."}


@router.get("/feed")
async def get_school_feed(
    tab: str = Query("mon_etablissement"),
    limit: int = Query(20),
    ctx: AuthenticatedUserContext = Depends(require_membership()),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Fil d'actualités réservé aux membres de l'établissement.
    Décision D8 : AUCUNE publicité tierce n'est affichée dans ce fil.
    """
    stmt = (
        select(PostModel)
        .where(PostModel.tenant_id == ctx.tenant_id)
        .order_by(PostModel.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    posts = res.scalars().all()

    return [
        {
            "id": str(p.id),
            "tenant_id": str(p.tenant_id),
            "author_id": str(p.author_id),
            "content": p.content,
            "type": p.type.value if hasattr(p.type, 'value') else str(p.type),
            "media_urls": p.media_urls,
            "is_sponsored": False,  # D8 : Ad-free pour membres
            "views_count": p.views_count,
            "created_at": p.created_at.isoformat(),
        }
        for p in posts
    ]