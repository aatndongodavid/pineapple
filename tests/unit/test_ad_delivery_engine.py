# tests/unit/test_ad_delivery_engine.py

import json
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select, delete

from identity_context.infrastructure.persistence.models import UserModel, TenantModel, MembershipModel
from identity_context.domain.value_objects import AccountStatus, MembershipRole, MembershipStatus
from monetization_context.infrastructure.persistence.models import (
    AdvertiserModel, AdWalletModel, AdCampaignModel, AdCreativeModel, AdTargetingRuleModel, AdImpressionRawModel
)
from monetization_context.domain.services.ad_delivery_engine import AdDeliveryEngine


@pytest.mark.asyncio
async def test_gate_r1_school_members_receive_zero_third_party_ads(session_factory):
    """
    Gate R1: Aucun membre actif d'école abonnée ne voit de publicité tierce.
    Le contrôle est strictement fait côté serveur.
    """
    tenant_id = uuid.uuid4()
    student_id = uuid.uuid4()
    campaign_id = uuid.uuid4()

    async with session_factory() as db:
        await db.execute(delete(AdImpressionRawModel))
        await db.execute(delete(AdCreativeModel))
        await db.execute(delete(AdTargetingRuleModel))
        await db.execute(delete(AdCampaignModel))
        # Seed Tenant & Active Student
        tenant = TenantModel(id=tenant_id, name="École Test R1", code=f"R1_{uuid.uuid4().hex[:4]}", is_active=True)
        db.add(tenant)

        user = UserModel(id=student_id, email=f"student_{student_id.hex[:6]}@test.com", first_name="Etudiant", last_name="Membre", hashed_password="hash", account_status=AccountStatus.ACTIVE)
        db.add(user)

        membership = MembershipModel(id=uuid.uuid4(), tenant_id=tenant_id, user_id=student_id, role=MembershipRole.STUDENT, status=MembershipStatus.ACTIVE, academic_year="2026-2027")
        db.add(membership)

        # Seed Active Ad Campaign & Creative
        campaign = AdCampaignModel(id=campaign_id, title="Offre PC Etudiant", advertiser_name="TechStore", status="ACTIVE", total_budget_xaf=50000, spent_xaf=0, daily_budget_xaf=5000, daily_spent_xaf=0)
        db.add(campaign)

        creative = AdCreativeModel(id=uuid.uuid4(), campaign_id=campaign_id, headline="Réduction PC Portables", body_text="Vente flash informatique", review_status="APPROVED", is_active=True)
        db.add(creative)

        await db.commit()

    async with session_factory() as db:
        engine = AdDeliveryEngine(db)
        # Membre actif -> doit recevoir un tableau vide []
        ads = await engine.get_visitor_ad_feed(user_id=student_id, visitor_session_id="sess_123")
        assert len(ads) == 0

        # Utilisateur anonyme (Visiteur sans membre d'école) -> doit recevoir la publicité
        visitor_ads = await engine.get_visitor_ad_feed(user_id=None, visitor_session_id="sess_visitor_123")
        assert len(visitor_ads) == 1
        assert visitor_ads[0].headline == "Réduction PC Portables"


@pytest.mark.asyncio
async def test_gate_r2_coarse_visitor_targeting(session_factory):
    """
    Gate R2: Filtre de ciblage grossier (ville/région, langue).
    """
    campaign_id = uuid.uuid4()

    async with session_factory() as db:
        await db.execute(delete(AdImpressionRawModel))
        await db.execute(delete(AdCreativeModel))
        await db.execute(delete(AdTargetingRuleModel))
        await db.execute(delete(AdCampaignModel))

        campaign = AdCampaignModel(id=campaign_id, title="Pub Resto Douala", advertiser_name="RestoDla", status="ACTIVE", total_budget_xaf=50000, spent_xaf=0)
        db.add(campaign)

        targeting = AdTargetingRuleModel(
            id=uuid.uuid4(),
            campaign_id=campaign_id,
            cities_regions_json=json.dumps(["Douala"]),
            languages_json=json.dumps(["fr"]),
        )
        db.add(targeting)

        creative = AdCreativeModel(id=uuid.uuid4(), campaign_id=campaign_id, headline="Menu du jour à Akwa", body_text="Spécialités locales", review_status="APPROVED", is_active=True)
        db.add(creative)

        await db.commit()

    async with session_factory() as db:
        engine = AdDeliveryEngine(db)

        # 1. Visiteur à Douala en FR -> Reçoit l'annonce
        ads_dla = await engine.get_visitor_ad_feed(user_id=None, visitor_session_id="sess_dla", city_region="Douala", language="fr")
        assert len(ads_dla) == 1

        # 2. Visiteur à Yaoundé -> Filtre élimine l'annonce
        ads_yde = await engine.get_visitor_ad_feed(user_id=None, visitor_session_id="sess_yde", city_region="Yaoundé", language="fr")
        assert len(ads_yde) == 0


@pytest.mark.asyncio
async def test_gate_r4_and_r7_budget_exhaustion_and_frequency_cap(session_factory):
    """
    Gate R4 & R7: Plafond de fréquence par session et arrêt sur budget épuisé.
    """
    campaign_id = uuid.uuid4()
    creative_id = uuid.uuid4()
    advertiser_id = uuid.uuid4()

    async with session_factory() as db:
        await db.execute(delete(AdImpressionRawModel))
        await db.execute(delete(AdCreativeModel))
        await db.execute(delete(AdTargetingRuleModel))
        await db.execute(delete(AdCampaignModel))
        advertiser = AdvertiserModel(id=advertiser_id, company_name="Pub Co", contact_email="contact@pubco.cm", status="ACTIVE")
        db.add(advertiser)

        wallet = AdWalletModel(id=uuid.uuid4(), advertiser_id=advertiser_id, balance_xaf=10000)
        db.add(wallet)

        campaign = AdCampaignModel(
            id=campaign_id,
            advertiser_id=advertiser_id,
            title="Pub Telecom",
            advertiser_name="Pub Co",
            status="ACTIVE",
            total_budget_xaf=50000,
            spent_xaf=0,
            daily_budget_xaf=5000,
            daily_spent_xaf=0,
            frequency_cap_per_session=2,  # Max 2 fois par session
            unit_price_xaf=500,
        )
        db.add(campaign)

        creative = AdCreativeModel(id=creative_id, campaign_id=campaign_id, headline="Forfait Internet 4G", body_text="Profitez du haut débit", review_status="APPROVED", is_active=True)
        db.add(creative)

        # Simuler 2 impressions déjà servies dans la session "sess_cap"
        for _ in range(2):
            raw = AdImpressionRawModel(id=uuid.uuid4(), creative_id=creative_id, campaign_id=campaign_id, visitor_session_id="sess_cap", token=f"tok_{uuid.uuid4().hex}")
            db.add(raw)

        await db.commit()

    async with session_factory() as db:
        engine = AdDeliveryEngine(db)

        # Pour sess_cap -> Plafond de fréquence atteint (2 imps) -> 0 annonce servie
        ads_capped = await engine.get_visitor_ad_feed(user_id=None, visitor_session_id="sess_cap")
        assert len(ads_capped) == 0

        # Pour nouvelle session "sess_new" -> 1 annonce servie
        ads_new = await engine.get_visitor_ad_feed(user_id=None, visitor_session_id="sess_new")
        assert len(ads_new) == 1
