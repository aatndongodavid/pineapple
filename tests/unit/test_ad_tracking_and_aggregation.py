# tests/unit/test_ad_tracking_and_aggregation.py

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select, delete

from monetization_context.infrastructure.persistence.models import (
    AdvertiserModel, AdWalletModel, AdCampaignModel, AdCreativeModel,
    AdImpressionRawModel, AdEventModel, AdStatsDailyModel
)
from monetization_context.domain.services.ad_token_service import AdTokenService
from monetization_context.domain.services.ad_tracking_service import AdTrackingService
from monetization_context.domain.services.ad_stats_aggregator import AdStatsAggregatorService


@pytest.mark.asyncio
async def test_gate_r5_impression_and_click_tracking_anti_replay(session_factory):
    """
    Gate R5: Enregistrement sécurisé des impressions/clics avec vérification anti-rejeu par jeton signé.
    """
    advertiser_id = uuid.uuid4()
    campaign_id = uuid.uuid4()
    creative_id = uuid.uuid4()
    visitor_session_id = f"sess_{uuid.uuid4().hex[:8]}"

    async with session_factory() as db:
        await db.execute(delete(AdEventModel))
        await db.execute(delete(AdImpressionRawModel))
        await db.execute(delete(AdStatsDailyModel))
        await db.execute(delete(AdCreativeModel))
        await db.execute(delete(AdCampaignModel))
        await db.execute(delete(AdWalletModel))
        await db.execute(delete(AdvertiserModel))

        # Seed advertiser, wallet, campaign, creative
        advertiser = AdvertiserModel(id=advertiser_id, company_name="AdTech Corp", contact_email="ads@adtech.cm", status="ACTIVE")
        db.add(advertiser)

        wallet = AdWalletModel(id=uuid.uuid4(), advertiser_id=advertiser_id, balance_xaf=50000)
        db.add(wallet)

        campaign = AdCampaignModel(
            id=campaign_id,
            advertiser_id=advertiser_id,
            title="Campagne Test R5",
            advertiser_name="AdTech Corp",
            target_url="https://adtech.cm/promo",
            status="ACTIVE",
            total_budget_xaf=100000,
            spent_xaf=0,
            daily_budget_xaf=10000,
            daily_spent_xaf=0,
            billing_model="CPM",
            unit_price_xaf=1000,
        )
        db.add(campaign)

        creative = AdCreativeModel(
            id=creative_id,
            campaign_id=campaign_id,
            headline="Offre Spéciale R5",
            body_text="Découvrez nos services",
            target_url="https://adtech.cm/promo",
            review_status="APPROVED",
            is_active=True,
        )
        db.add(creative)

        await db.commit()

    # Générer un jeton d'impression valide
    token = AdTokenService.generate_impression_token(
        creative_id=creative_id,
        campaign_id=campaign_id,
        visitor_session_id=visitor_session_id,
        billing_model="CPM",
        unit_price_xaf=1000,
        advertiser_id=advertiser_id,
    )

    async with session_factory() as db:
        tracking_service = AdTrackingService(db)

        # 1. Enregistrement d'une première impression -> Doit réussir
        success, reason = await tracking_service.record_impression(token=token, ip="192.168.1.10", user_agent="Mozilla/5.0")
        assert success is True
        assert reason == "SUCCESS"

        await db.commit()

    async with session_factory() as db:
        tracking_service = AdTrackingService(db)

        # 2. Rejeu du même jeton d'impression -> Doit échouer avec TOKEN_ALREADY_USED
        success_replay, reason_replay = await tracking_service.record_impression(token=token, ip="192.168.1.10")
        assert success_replay is False
        assert reason_replay == "TOKEN_ALREADY_USED"

        # 3. Enregistrement d'un clic via le jeton -> Doit renvoyer l'URL cible
        click_success, target_url, click_reason = await tracking_service.record_click_and_resolve_url(
            token=token, ip="192.168.1.10"
        )
        assert click_success is True
        assert target_url == "https://adtech.cm/promo"
        assert click_reason == "SUCCESS"


@pytest.mark.asyncio
async def test_gate_r12_daily_stats_aggregation_and_reporting(session_factory):
    """
    Gate R12: Agrégation des statistiques journalières et calcul du CTR / dépenses.
    """
    campaign_id = uuid.uuid4()
    creative_id = uuid.uuid4()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    async with session_factory() as db:
        await db.execute(delete(AdStatsDailyModel))
        aggregator = AdStatsAggregatorService(db)

        # Simuler 100 impressions, 5 clics, et 5000 XAF de dépense
        await aggregator.increment_daily_stat(
            campaign_id=campaign_id,
            creative_id=creative_id,
            stat_date=today_str,
            impressions_delta=100,
            clicks_delta=5,
            spent_delta_xaf=5000,
        )
        await db.commit()

    async with session_factory() as db:
        aggregator = AdStatsAggregatorService(db)
        stats = await aggregator.get_campaign_stats(campaign_id=campaign_id)

        assert stats["total_impressions"] == 100
        assert stats["total_clicks"] == 5
        assert stats["total_spent_xaf"] == 5000
        assert stats["ctr_percent"] == 5.0  # (5/100)*100
        assert len(stats["daily_breakdown"]) == 1
        assert stats["daily_breakdown"][0]["stat_date"] == today_str
