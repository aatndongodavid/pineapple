# backend/src/api/v1/ads_router.py

import uuid
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Header, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from monetization_context.infrastructure.persistence.models import (
    AdCreativeModel, AdCampaignModel, AdUserFeedbackModel
)
from monetization_context.domain.services.ad_delivery_engine import AdDeliveryEngine, VisitorAdDTO
from monetization_context.domain.services.ad_tracking_service import AdTrackingService
from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.security import AuthenticatedUserContext, get_user_context

router = APIRouter(prefix="/ads", tags=["Advertisements Engine"])


class VisitorAdResponseDTO(BaseModel):
    id: str
    campaign_id: str
    headline: str
    body_text: str
    image_url: Optional[str] = None
    cta_text: str = "En savoir plus"
    target_url: Optional[str] = None
    impression_token: str
    advertiser_name: str
    is_sponsored: bool = True


class AdImpressionRequestDTO(BaseModel):
    token: str


class AdFeedbackRequestDTO(BaseModel):
    creative_id: uuid.UUID
    visitor_session_id: str
    feedback_type: str = Field(..., description="HIDE ou REPORT")
    reason: Optional[str] = None
    details: Optional[str] = None


@router.get("/feed", response_model=List[VisitorAdResponseDTO])
async def get_visitor_ad_feed(
    request: Request,
    visitor_session_id: Optional[str] = Header(None, alias="X-Visitor-Session-ID"),
    city_region: Optional[str] = None,
    language: Optional[str] = "fr",
    user: Optional[AuthenticatedUserContext] = Depends(get_user_context),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Renvoie le fil de publicités réservé exclusivement aux Visiteurs (Gate R1).
    Les membres actifs d'une école reçoivent toujours un tableau vide [].
    """
    session_id = visitor_session_id or (request.client.host if request.client else "anon_session")
    user_id = user.user_id if user else None

    delivery_engine = AdDeliveryEngine(db)
    ads: List[VisitorAdDTO] = await delivery_engine.get_visitor_ad_feed(
        user_id=user_id,
        visitor_session_id=session_id,
        city_region=city_region,
        language=language,
        limit=5,
    )

    return [VisitorAdResponseDTO(**ad.to_dict()) for ad in ads]


@router.post("/impression", status_code=status.HTTP_200_OK)
async def record_ad_impression(
    dto: AdImpressionRequestDTO,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Consigne une impression avec vérification anti-rejeu par jeton HMAC (Gate R5).
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    tracking_service = AdTrackingService(db)
    success, reason = await tracking_service.record_impression(
        token=dto.token,
        ip=client_ip,
        user_agent=user_agent,
    )

    if not success:
        if reason == "TOKEN_ALREADY_USED":
            raise HTTPException(status_code=409, detail="Impression déjà comptabilisée (anti-rejeu)")
        raise HTTPException(status_code=400, detail="Jeton d'impression invalide ou expiré")

    await db.commit()
    return {"status": "SUCCESS", "message": "Impression enregistrée"}


@router.get("/click/{token}")
async def handle_ad_click(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Enregistre le clic, débite le budget CPC si applicable, et redirige de façon sécurisée (Gate R5).
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    tracking_service = AdTrackingService(db)
    success, target_url, reason = await tracking_service.record_click_and_resolve_url(
        token=token,
        ip=client_ip,
        user_agent=user_agent,
    )

    if not success or not target_url:
        raise HTTPException(status_code=400, detail=f"Échec du traitement du clic : {reason}")

    await db.commit()

    # Redirection HTTP 307
    return RedirectResponse(url=target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_visitor_feedback(
    dto: AdFeedbackRequestDTO,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Enregistre le masquage ou le signalement d'une publicité (Gate R11 Anti-fraude).
    Si le nombre de signalements dépasse 5, la création publicitaire est auto-suspendue.
    """
    if dto.feedback_type not in ["HIDE", "REPORT"]:
        raise HTTPException(status_code=400, detail="feedback_type doit être HIDE ou REPORT")

    feedback = AdUserFeedbackModel(
        id=uuid.uuid4(),
        creative_id=dto.creative_id,
        visitor_session_id=dto.visitor_session_id,
        feedback_type=dto.feedback_type,
        reason=dto.reason,
        details=dto.details,
    )
    db.add(feedback)
    await db.flush()

    # Vérification du seuil d'auto-suspension (Gate R11: > 5 signalements)
    if dto.feedback_type == "REPORT":
        stmt_count = select(func.count(AdUserFeedbackModel.id)).where(
            AdUserFeedbackModel.creative_id == dto.creative_id,
            AdUserFeedbackModel.feedback_type == "REPORT",
        )
        res = await db.execute(stmt_count)
        report_count = res.scalar() or 0

        if report_count > 5:
            creative = await db.get(AdCreativeModel, dto.creative_id)
            if creative and creative.is_active:
                creative.is_active = False
                creative.review_status = "REJECTED"
                creative.rejection_reason = "Auto-suspendu suite à plus de 5 signalements visiteurs (Gate R11)"

    await db.commit()
    return {"status": "SUCCESS", "feedback_type": dto.feedback_type}
