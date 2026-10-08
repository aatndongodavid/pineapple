# backend/src/api/v1/advertiser_router.py

import json
import csv
import io
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from monetization_context.infrastructure.persistence.models import (
    AdvertiserModel, AdWalletModel, AdCampaignModel, AdCreativeModel, AdTargetingRuleModel, WalletTransactionModel
)
from monetization_context.domain.services.ad_wallet_service import AdWalletService
from monetization_context.domain.services.ad_policy_engine import AdPolicyEngine
from monetization_context.domain.services.ad_stats_aggregator import AdStatsAggregatorService
from shared_kernel.infrastructure.database import get_db_session
from shared_kernel.infrastructure.security import AuthenticatedUserContext, get_user_context

router = APIRouter(prefix="/advertiser", tags=["Advertiser Portal"])


# DTOs
class AdvertiserRegisterDTO(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255)
    contact_email: str = Field(..., min_length=5, max_length=255)
    phone_number: Optional[str] = None
    tax_id: Optional[str] = None


class WalletTopupDTO(BaseModel):
    amount_xaf: int = Field(..., gt=0)
    payment_method: str = "ORANGE_MONEY"  # ORANGE_MONEY, MTN_MOMO, CARD
    idempotency_key: Optional[str] = None


class CampaignCreateDTO(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    target_url: str
    total_budget_xaf: int = Field(..., gt=0)
    daily_budget_xaf: int = Field(..., gt=0)
    billing_model: str = "CPM"  # CPM, CPC
    unit_price_xaf: int = Field(..., gt=0)
    frequency_cap_per_session: int = Field(default=3, gt=0)
    cities_regions: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)


class CreativeSubmitDTO(BaseModel):
    headline: str = Field(..., min_length=3, max_length=200)
    body_text: str = Field(..., min_length=5)
    image_url: Optional[str] = None
    cta_text: str = Field(default="En savoir plus", max_length=100)
    target_url: Optional[str] = None


async def get_current_advertiser(
    user: AuthenticatedUserContext = Depends(get_user_context),
    db: AsyncSession = Depends(get_db_session),
) -> AdvertiserModel:
    """
    Récupère le profil annonceur lié à l'utilisateur connecté ou lève une 403 (Gate R9).
    """
    if not user or not user.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentification requise")

    stmt = select(AdvertiserModel).where(AdvertiserModel.user_id == user.user_id)
    res = await db.execute(stmt)
    advertiser = res.scalars().first()

    if not advertiser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte annonceur non trouvé")
    if advertiser.status == "SUSPENDED":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte annonceur suspendu")

    return advertiser


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_advertiser(
    dto: AdvertiserRegisterDTO,
    user: AuthenticatedUserContext = Depends(get_user_context),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Inscrit un nouvel annonceur et initialise son portefeuille prépayé XAF (Gate R10).
    """
    if not user or not user.user_id:
        raise HTTPException(status_code=401, detail="Authentification requise")

    # Vérifier si déjà inscrit
    stmt = select(AdvertiserModel).where(AdvertiserModel.user_id == user.user_id)
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Un profil annonceur existe déjà pour cet utilisateur")

    advertiser = AdvertiserModel(
        id=uuid.uuid4(),
        user_id=user.user_id,
        company_name=dto.company_name,
        contact_email=dto.contact_email,
        phone_number=dto.phone_number,
        tax_id=dto.tax_id,
        status="ACTIVE",
    )
    db.add(advertiser)

    # Initialiser le portefeuille prépayé à 0 XAF
    wallet = AdWalletModel(
        id=uuid.uuid4(),
        advertiser_id=advertiser.id,
        balance_xaf=0,
    )
    db.add(wallet)

    await db.commit()
    return {"advertiser_id": str(advertiser.id), "wallet_id": str(wallet.id), "status": "ACTIVE"}


@router.get("/me")
async def get_advertiser_profile(
    advertiser: AdvertiserModel = Depends(get_current_advertiser),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Récupère le profil annonceur courant et le solde du portefeuille.
    """
    stmt = select(AdWalletModel).where(AdWalletModel.advertiser_id == advertiser.id)
    res = await db.execute(stmt)
    wallet = res.scalars().first()

    return {
        "id": str(advertiser.id),
        "company_name": advertiser.company_name,
        "contact_email": advertiser.contact_email,
        "phone_number": advertiser.phone_number,
        "status": advertiser.status,
        "balance_xaf": wallet.balance_xaf if wallet else 0,
    }


@router.post("/wallet/topup")
async def topup_wallet(
    dto: WalletTopupDTO,
    advertiser: AdvertiserModel = Depends(get_current_advertiser),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Crédite le portefeuille prépayé de l'annonceur (Journal immuable, Gate R10).
    """
    stmt = select(AdWalletModel).where(AdWalletModel.advertiser_id == advertiser.id)
    res = await db.execute(stmt)
    wallet = res.scalars().first()

    if not wallet:
        raise HTTPException(status_code=404, detail="Portefeuille non trouvé")

    wallet_service = AdWalletService(db)
    ref_id = dto.idempotency_key or f"topup_{uuid.uuid4().hex[:12]}"
    tx, success, reason = await wallet_service.credit_wallet(
        wallet_id=wallet.id,
        amount_xaf=dto.amount_xaf,
        reference_id=ref_id,
        description=f"Rechargement via {dto.payment_method}",
    )

    if not success:
        raise HTTPException(status_code=400, detail=reason)

    await db.commit()
    return {
        "transaction_id": str(tx.id),
        "new_balance_xaf": wallet.balance_xaf,
        "amount_credited_xaf": dto.amount_xaf,
        "status": "SUCCESS",
    }


@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    dto: CampaignCreateDTO,
    advertiser: AdvertiserModel = Depends(get_current_advertiser),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Crée une nouvelle campagne publicitaire pour l'annonceur connecté (Gate R9 IDOR).
    """
    # Valider l'URL cible
    valid_scheme, err = AdPolicyEngine.validate_target_url(dto.target_url)
    if not valid_scheme:
        raise HTTPException(status_code=400, detail=f"URL cible invalide : {err}")

    campaign = AdCampaignModel(
        id=uuid.uuid4(),
        advertiser_id=advertiser.id,
        title=dto.title,
        advertiser_name=advertiser.company_name,
        target_url=dto.target_url,
        status="ACTIVE",
        total_budget_xaf=dto.total_budget_xaf,
        spent_xaf=0,
        daily_budget_xaf=dto.daily_budget_xaf,
        daily_spent_xaf=0,
        billing_model=dto.billing_model,
        unit_price_xaf=dto.unit_price_xaf,
        frequency_cap_per_session=dto.frequency_cap_per_session,
    )
    db.add(campaign)

    targeting = AdTargetingRuleModel(
        id=uuid.uuid4(),
        campaign_id=campaign.id,
        cities_regions_json=json.dumps(dto.cities_regions),
        languages_json=json.dumps(dto.languages),
    )
    db.add(targeting)

    await db.commit()
    return {"campaign_id": str(campaign.id), "status": "ACTIVE", "title": campaign.title}


@router.get("/campaigns")
async def list_campaigns(
    advertiser: AdvertiserModel = Depends(get_current_advertiser),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Liste les campagnes appartenant STRICTEMENT à l'annonceur connecté (Gate R9).
    """
    stmt = select(AdCampaignModel).where(AdCampaignModel.advertiser_id == advertiser.id)
    res = await db.execute(stmt)
    campaigns = res.scalars().all()

    return [
        {
            "id": str(c.id),
            "title": c.title,
            "status": c.status,
            "total_budget_xaf": c.total_budget_xaf,
            "spent_xaf": c.spent_xaf,
            "daily_budget_xaf": c.daily_budget_xaf,
            "daily_spent_xaf": c.daily_spent_xaf,
            "billing_model": c.billing_model,
            "unit_price_xaf": c.unit_price_xaf,
            "created_at": c.created_at.isoformat(),
        }
        for c in campaigns
    ]


@router.post("/campaigns/{campaign_id}/creatives", status_code=status.HTTP_201_CREATED)
async def submit_creative(
    campaign_id: uuid.UUID,
    dto: CreativeSubmitDTO,
    advertiser: AdvertiserModel = Depends(get_current_advertiser),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Soumet un visuel pub pour une campagne avec vérification automatique de politique (Gate R3, Gate R9 IDOR).
    """
    # 1. Contrôle d'accès IDOR (Gate R9)
    campaign = await db.get(AdCampaignModel, campaign_id)
    if not campaign or campaign.advertiser_id != advertiser.id:
        raise HTTPException(status_code=403, detail="Accès refusé à cette campagne")

    target_url = dto.target_url or campaign.target_url
    if target_url:
        valid_url, err = AdPolicyEngine.validate_target_url(target_url)
        if not valid_url:
            raise HTTPException(status_code=400, detail=f"URL cible invalide : {err}")

    # 2. Vérification automatisée de la politique de modération (Gate R3)
    policy_engine = AdPolicyEngine(db)
    is_passed, violation_reason = await policy_engine.check_creative_policy(
        headline=dto.headline, body_text=dto.body_text
    )

    review_status = "APPROVED" if is_passed else "REJECTED"
    rejection_reason = None if is_passed else f"Refus automatique de politique : {violation_reason}"

    creative = AdCreativeModel(
        id=uuid.uuid4(),
        campaign_id=campaign_id,
        headline=dto.headline,
        body_text=dto.body_text,
        image_url=dto.image_url,
        cta_text=dto.cta_text,
        target_url=target_url,
        review_status=review_status,
        rejection_reason=rejection_reason,
        is_active=is_passed,
    )
    db.add(creative)
    await db.commit()

    return {
        "creative_id": str(creative.id),
        "review_status": creative.review_status,
        "rejection_reason": creative.rejection_reason,
        "is_active": creative.is_active,
    }


@router.get("/campaigns/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: uuid.UUID,
    format: Optional[str] = None,
    advertiser: AdvertiserModel = Depends(get_current_advertiser),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Récupère le rapport de performance d'une campagne avec export CSV optionnel (Gate R9, Gate R12).
    """
    campaign = await db.get(AdCampaignModel, campaign_id)
    if not campaign or campaign.advertiser_id != advertiser.id:
        raise HTTPException(status_code=403, detail="Accès refusé à cette campagne")

    aggregator = AdStatsAggregatorService(db)
    stats_data = await aggregator.get_campaign_stats(campaign_id=campaign_id)

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Creative ID", "Impressions", "Clicks", "Spent XAF", "CTR %"])
        for row in stats_data.get("daily_breakdown", []):
            writer.writerow([
                row["stat_date"],
                row["creative_id"],
                row["impressions"],
                row["clicks"],
                row["spent_xaf"],
                row["ctr_percent"],
            ])
        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=campaign_{campaign_id}_stats.csv"},
        )

    return stats_data
