# tests/unit/test_ad_moderation_and_policy.py

import uuid
import pytest
from sqlalchemy import select

from monetization_context.infrastructure.persistence.models import AdCampaignModel, AdCreativeModel, AdReviewEventModel
from monetization_context.domain.services.ad_policy_engine import AdPolicyEngine
from monetization_context.domain.services.creative_review_service import CreativeReviewService


def test_gate_r6_url_validation_policy():
    """
    Gate R6: Seuls les protocoles http:// et https:// sont acceptés.
    Rejet strict des schémas javascript:, data:, file:, etc.
    """
    engine = AdPolicyEngine()

    ok, _ = engine.validate_target_url("https://www.example.com/promo")
    assert ok is True

    ok2, _ = engine.validate_target_url("http://sub.company.cm/landing")
    assert ok2 is True

    # Malicious or unsupported schemes
    ok_js, reason_js = engine.validate_target_url("javascript:alert(1)")
    assert ok_js is False
    assert "non autorisé ('javascript')" in reason_js

    ok_data, reason_data = engine.validate_target_url("data:text/html;base64,PHNjcmlwdD4=")
    assert ok_data is False

    ok_file, _ = engine.validate_target_url("file:///etc/passwd")
    assert ok_file is False


@pytest.mark.asyncio
async def test_gate_r3_prohibited_categories_and_keyword_moderation(session_factory):
    """
    Gate R3: Les catégories interdites (tabac, casino, etc.) sont rejetées automatiquement.
    """
    campaign_id = uuid.uuid4()
    async with session_factory() as db:
        cmp_model = AdCampaignModel(
            id=campaign_id,
            title="Campagne Test Modération",
            advertiser_name="Annonceur Test",
            status="ACTIVE",
        )
        db.add(cmp_model)
        await db.commit()

    # 1. Création avec mot-clé interdit (casino / paris sports) -> Rejeté automatiquement
    async with session_factory() as db:
        service = CreativeReviewService(db)
        creative, is_ok, msg = await service.submit_creative_for_review(
            campaign_id=campaign_id,
            headline="Gagnez gros sur 1XBet casino",
            body_text="Inscrivez-vous pour des paris sportifs en ligne",
            target_url="https://www.bet-test.cm",
        )
        assert is_ok is False
        assert creative.review_status == "REJECTED"
        assert "1xbet" in creative.rejection_reason.lower() or "casino" in creative.rejection_reason.lower()
        await db.commit()

    # 2. Création valide -> PENDING_REVIEW
    async with session_factory() as db:
        service = CreativeReviewService(db)
        creative2, is_ok2, msg2 = await service.submit_creative_for_review(
            campaign_id=campaign_id,
            headline="Formation en Informatique et Digital",
            body_text="Rejoignez notre centre de formation professionnelle à Douala",
            target_url="https://www.formation-digital.cm",
        )
        assert is_ok2 is True
        assert creative2.review_status == "PENDING_REVIEW"
        await db.commit()

    # 3. Modération manuelle par administrateur
    reviewer_id = uuid.uuid4()
    async with session_factory() as db:
        service = CreativeReviewService(db)
        approved_crt = await service.review_creative_by_admin(
            creative_id=creative2.id,
            reviewer_user_id=reviewer_id,
            new_status="APPROVED",
            reason="Contenu conforme",
        )
        assert approved_crt.review_status == "APPROVED"
        assert approved_crt.is_active is True
        await db.commit()

    # Vérification des événements de revue
    async with session_factory() as db:
        res = await db.execute(select(AdReviewEventModel).where(AdReviewEventModel.creative_id == creative2.id))
        events = res.scalars().all()
        assert len(events) >= 2
        statuses = [e.new_status for e in events]
        assert "PENDING_REVIEW" in statuses
        assert "APPROVED" in statuses
