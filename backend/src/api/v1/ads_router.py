import uuid
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from monetization_context.infrastructure.persistence.models import AdCampaignModel, AdCreativeModel, AdEventModel
from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.security import AuthenticatedUserContext, get_user_context

router = APIRouter(prefix="/ads", tags=["Advertisements"])


class AdCreativeDTO(BaseModel):
    id: str
    campaign_id: str
    headline: str
    body_text: str
    image_url: Optional[str] = None
    cta_text: str
    target_url: Optional[str] = None


class AdEventRequestDTO(BaseModel):
    creative_id: str
    event_type: str  # IMPRESSION, CLICK


@router.get("/feed", response_model=List[AdCreativeDTO])
async def get_visitor_ad_feed(
    db: AsyncSession = Depends(get_db_session),
):
    """
    Renvoie le fil de publicités réservé aux utilisateurs Visiteurs.
    """
    stmt = (
        select(AdCreativeModel, AdCampaignModel.target_url)
        .join(AdCampaignModel, AdCreativeModel.campaign_id == AdCampaignModel.id)
        .where(
            AdCreativeModel.is_active.is_(True),
            AdCampaignModel.status == "ACTIVE",
        )
        .order_by(AdCreativeModel.created_at.desc())
        .limit(20)
    )

    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for creative, target_url in rows:
        items.append(
            AdCreativeDTO(
                id=str(creative.id),
                campaign_id=str(creative.campaign_id),
                headline=creative.headline,
                body_text=creative.body_text,
                image_url=creative.image_url,
                cta_text=creative.cta_text,
                target_url=target_url,
            )
        )
    return items


@router.post("/events", status_code=status.HTTP_201_CREATED)
async def track_ad_event(
    dto: AdEventRequestDTO,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Enregistre une impression ou un clic sur une publicité.
    """
    if dto.event_type not in ["IMPRESSION", "CLICK"]:
        raise HTTPException(status_code=400, detail="event_type invalide")

    client_ip = request.client.host if request.client else "127.0.0.1"

    ad_event = AdEventModel(
        id=uuid.uuid4(),
        creative_id=uuid.UUID(dto.creative_id),
        event_type=dto.event_type,
        ip=client_ip,
        created_at=datetime.now(timezone.utc),
    )
    db.add(ad_event)
    await db.commit()
    return {"status": "ok"}
