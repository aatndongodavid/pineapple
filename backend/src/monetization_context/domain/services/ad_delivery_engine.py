# backend/src/monetization_context/domain/services/ad_delivery_engine.py

import json
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from identity_context.infrastructure.persistence.models import MembershipModel
from identity_context.domain.value_objects import MembershipStatus
from monetization_context.infrastructure.persistence.models import (
    AdCampaignModel, AdCreativeModel, AdTargetingRuleModel, AdWalletModel, AdImpressionRawModel
)
from monetization_context.domain.services.ad_token_service import AdTokenService

logger = logging.getLogger("AdDeliveryEngine")


class VisitorAdDTO:
    def __init__(
        self,
        creative_id: str,
        campaign_id: str,
        headline: str,
        body_text: str,
        image_url: Optional[str],
        cta_text: str,
        target_url: Optional[str],
        impression_token: str,
        advertiser_name: str,
    ):
        self.creative_id = creative_id
        self.campaign_id = campaign_id
        self.headline = headline
        self.body_text = body_text
        self.image_url = image_url
        self.cta_text = cta_text
        self.target_url = target_url
        self.impression_token = impression_token
        self.advertiser_name = advertiser_name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.creative_id,
            "campaign_id": self.campaign_id,
            "headline": self.headline,
            "body_text": self.body_text,
            "image_url": self.image_url,
            "cta_text": self.cta_text,
            "target_url": self.target_url,
            "impression_token": self.impression_token,
            "advertiser_name": self.advertiser_name,
            "is_sponsored": True,
        }


class AdDeliveryEngine:
    """
    Moteur de sélection et de diffusion des annonces publicitaires ciblées sur les visiteurs.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def user_is_school_member(self, user_id: Optional[uuid.UUID]) -> bool:
        """
        Vérifie côté serveur si l'utilisateur est un membre actif d'un établissement (Gate R1).
        Si True, l'utilisateur ne doit VOIR AUCUNE publicité tierce.
        """
        if not user_id:
            return False

        stmt = select(func.count(MembershipModel.id)).where(
            MembershipModel.user_id == user_id,
            MembershipModel.status == MembershipStatus.ACTIVE,
        )
        res = await self.db.execute(stmt)
        count = res.scalar_one() or 0
        return count > 0

    async def get_visitor_ad_feed(
        self,
        user_id: Optional[uuid.UUID],
        visitor_session_id: str,
        city_region: Optional[str] = None,
        language: str = "fr",
        device_type: str = "mobile",
        limit: int = 5,
        current_dt: Optional[datetime] = None,
    ) -> List[VisitorAdDTO]:
        """
        Génère le fil de publicités pour les visiteurs (Gate R1, R2, R4, R7, R8).
        """
        # 1. R1: Contrôle d'exclusion stricte pour les membres d'écoles
        if user_id and await self.user_is_school_member(user_id):
            logger.info(f"Utilisateur {user_id} est membre actif d'une école -> 0 publicité tierce servie (Gate R1).")
            return []

        dt = current_dt or datetime.now(timezone.utc)
        cur_hour = dt.hour

        # 2. Récupérer toutes les créations APPROVED et campagnes ACTIVE
        stmt = (
            select(AdCreativeModel, AdCampaignModel, AdWalletModel)
            .join(AdCampaignModel, AdCreativeModel.campaign_id == AdCampaignModel.id)
            .outerjoin(AdWalletModel, AdCampaignModel.advertiser_id == AdWalletModel.advertiser_id)
            .where(
                AdCreativeModel.is_active == True,
                AdCreativeModel.review_status == "APPROVED",
                AdCampaignModel.status == "ACTIVE",
            )
        )
        res = await self.db.execute(stmt)
        rows = res.all()

        eligible_items: List[Tuple[AdCreativeModel, AdCampaignModel, float]] = []

        for creative, campaign, wallet in rows:
            # 3. R4: Vérification des budgets et du solde du portefeuille
            if campaign.spent_xaf >= campaign.total_budget_xaf:
                continue
            if campaign.daily_spent_xaf >= campaign.daily_budget_xaf:
                continue

            # Solde portefeuille si annonceur rattaché
            if wallet and wallet.balance_xaf < campaign.unit_price_xaf:
                continue

            # 4. R2: Ciblage grossier (Targeting rules)
            target_stmt = select(AdTargetingRuleModel).where(AdTargetingRuleModel.campaign_id == campaign.id)
            t_res = await self.db.execute(target_stmt)
            target_rule = t_res.scalars().first()

            if target_rule:
                # Filtrage Ville/Région
                cities = json.loads(target_rule.cities_regions_json or "[]")
                if cities and city_region and city_region not in cities:
                    continue

                # Filtrage Langue
                langs = json.loads(target_rule.languages_json or "[]")
                if langs and language not in langs:
                    continue

                # Filtrage Appareil
                devices = json.loads(target_rule.device_types_json or "[]")
                if devices and device_type not in devices:
                    continue

                # Filtrage Heure
                hours = json.loads(target_rule.hours_of_day_json or "[]")
                if hours and cur_hour not in hours:
                    continue

            # 5. R7: Plafond de fréquence par session (Frequency Capping)
            imp_count_stmt = select(func.count(AdImpressionRawModel.id)).where(
                AdImpressionRawModel.creative_id == creative.id,
                AdImpressionRawModel.visitor_session_id == visitor_session_id,
            )
            imp_res = await self.db.execute(imp_count_stmt)
            session_imps = imp_res.scalar_one() or 0
            if session_imps >= campaign.frequency_cap_per_session:
                continue

            # 6. R8: Pacing horaire
            pacing_weight = 1.0
            if campaign.pacing_enabled:
                hourly_budget = campaign.daily_budget_xaf / 24.0
                # Si la dépense du jour dépasse le pro-rata horaire, réduire le poids de sélection
                expected_spent = (cur_hour + 1) * hourly_budget
                if campaign.daily_spent_xaf > expected_spent:
                    pacing_weight = 0.2  # Pénaliser la priorité pour étaler sur la journée

            # Calcul du score d'enchère simplifiée (Priorité CPM/CPC * poids pacing * facteur aléatoire d'exploration)
            effective_bid = campaign.unit_price_xaf * pacing_weight
            exploration_score = random.uniform(0.8, 1.2)
            final_score = effective_bid * exploration_score

            eligible_items.append((creative, campaign, final_score))

        # Tri par score décroissant
        eligible_items.sort(key=lambda x: x[2], reverse=True)

        # 7. Sélection avec contrainte de non-consécutivité par campagne
        selected_ads: List[VisitorAdDTO] = []
        last_campaign_id = None

        for creative, campaign, score in eligible_items:
            if len(selected_ads) >= limit:
                break
            if campaign.id == last_campaign_id and len(eligible_items) > 1:
                continue

            # Générer le jeton d'impression signé HMAC
            token = AdTokenService.generate_impression_token(
                creative_id=creative.id,
                campaign_id=campaign.id,
                visitor_session_id=visitor_session_id,
                unit_price_xaf=campaign.unit_price_xaf,
                billing_model=campaign.billing_model,
                advertiser_id=campaign.advertiser_id,
            )

            ad_dto = VisitorAdDTO(
                creative_id=str(creative.id),
                campaign_id=str(campaign.id),
                headline=creative.headline,
                body_text=creative.body_text,
                image_url=creative.image_url,
                cta_text=creative.cta_text,
                target_url=creative.target_url or campaign.target_url,
                impression_token=token,
                advertiser_name=campaign.advertiser_name,
            )
            selected_ads.append(ad_dto)
            last_campaign_id = campaign.id

        return selected_ads
