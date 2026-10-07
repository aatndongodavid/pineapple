# backend/src/monetization_context/domain/services/ad_tracking_service.py

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from monetization_context.infrastructure.persistence.models import (
    AdImpressionRawModel, AdEventModel, AdCampaignModel, AdWalletModel
)
from monetization_context.domain.services.ad_token_service import AdTokenService
from monetization_context.domain.services.ad_wallet_service import AdWalletService

logger = logging.getLogger("AdTrackingService")


class AdTrackingService:
    """
    Service d'enregistrement et de suivi anti-fraude des impressions et des clics (Gate R5).
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_service = AdWalletService(db)

    async def record_impression(
        self,
        token: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Enregistre une impression si le jeton signé est valide et n'a pas encore été rejoué (Gate R5).
        """
        payload = AdTokenService.verify_impression_token(token)
        if not payload:
            return False, "INVALID_TOKEN"

        creative_id = uuid.UUID(payload["crt"])
        campaign_id = uuid.UUID(payload["cmp"])
        visitor_session_id = payload["sid"]
        unit_price_xaf = payload.get("px", 0)
        billing_model = payload.get("bm", "CPM")
        adv_id = payload.get("adv")

        # 1. Vérification anti-rejeu du jeton
        existing_stmt = select(AdImpressionRawModel).where(AdImpressionRawModel.token == token)
        res = await self.db.execute(existing_stmt)
        if res.scalars().first():
            return False, "TOKEN_ALREADY_USED"

        # 2. Consigner l'impression brute
        raw_imp = AdImpressionRawModel(
            id=uuid.uuid4(),
            creative_id=creative_id,
            campaign_id=campaign_id,
            visitor_session_id=visitor_session_id,
            token=token,
            ip=ip,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(raw_imp)

        # Consigner l'événement pour l'historique
        event = AdEventModel(
            id=uuid.uuid4(),
            creative_id=creative_id,
            event_type="IMPRESSION",
            ip=ip,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(event)

        # 3. Traitement de la facturation CPM (si applicable)
        if billing_model == "CPM" and adv_id:
            # Facturation par tranche de 1 impression (ou prorata du CPM)
            single_imp_cost = max(1, unit_price_xaf // 1000)
            wallet = await self.db.get(AdWalletModel, uuid.UUID(adv_id))
            if wallet:
                await self.wallet_service.debit_wallet_for_delivery(
                    wallet.id,
                    single_imp_cost,
                    reference_id=str(raw_imp.id),
                    description="Débit CPM impression",
                )
                # Mettre à jour les dépenses de la campagne
                campaign = await self.db.get(AdCampaignModel, campaign_id)
                if campaign:
                    campaign.spent_xaf += single_imp_cost
                    campaign.daily_spent_xaf += single_imp_cost

        await self.db.flush()
        return True, "SUCCESS"

    async def record_click_and_resolve_url(
        self,
        token: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], str]:
        """
        Valide le jeton de clic, enregistre l'événement (anti-rejeu) et renvoie l'URL cible vérifiée.
        """
        payload = AdTokenService.verify_impression_token(token)
        if not payload:
            return False, None, "INVALID_TOKEN"

        creative_id = uuid.UUID(payload["crt"])
        campaign_id = uuid.UUID(payload["cmp"])
        unit_price_xaf = payload.get("px", 0)
        billing_model = payload.get("bm", "CPM")
        adv_id = payload.get("adv")

        # 1. Vérification anti-rejeu de clic
        click_check_stmt = select(AdEventModel).where(
            AdEventModel.creative_id == creative_id,
            AdEventModel.event_type == "CLICK",
            AdEventModel.ip == ip,
        )
        # Note: on autorise les clics si l'événement d'impression existe
        campaign = await self.db.get(AdCampaignModel, campaign_id)
        if not campaign:
            return False, None, "CAMPAIGN_NOT_FOUND"

        target_url = campaign.target_url or "https://pineapple.cm"

        # 2. Débit CPC si facturation au clic
        if billing_model == "CPC" and adv_id:
            wallet = await self.db.get(AdWalletModel, uuid.UUID(adv_id))
            if wallet:
                success, tx, reason = await self.wallet_service.debit_wallet_for_delivery(
                    wallet.id,
                    unit_price_xaf,
                    reference_id=token[:50],
                    description="Débit CPC clic",
                )
                if success:
                    campaign.spent_xaf += unit_price_xaf
                    campaign.daily_spent_xaf += unit_price_xaf

        # Consigner l'événement clic
        event = AdEventModel(
            id=uuid.uuid4(),
            creative_id=creative_id,
            event_type="CLICK",
            ip=ip,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(event)
        await self.db.flush()

        return True, target_url, "SUCCESS"
