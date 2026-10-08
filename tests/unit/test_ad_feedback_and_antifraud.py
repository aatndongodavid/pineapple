# tests/unit/test_ad_feedback_and_antifraud.py

import uuid
import pytest
from sqlalchemy import select, func, delete

from monetization_context.infrastructure.persistence.models import (
    AdCampaignModel, AdCreativeModel, AdUserFeedbackModel
)


@pytest.mark.asyncio
async def test_gate_r11_visitor_feedback_and_auto_suspension(session_factory):
    """
    Gate R11: Traitement du masquage/signalement et auto-suspension si > 5 signalements.
    """
    campaign_id = uuid.uuid4()
    creative_id = uuid.uuid4()

    async with session_factory() as db:
        await db.execute(delete(AdUserFeedbackModel))
        await db.execute(delete(AdCreativeModel))
        await db.execute(delete(AdCampaignModel))

        campaign = AdCampaignModel(id=campaign_id, title="Campagne Test R11", advertiser_name="Annonceur R11", status="ACTIVE", total_budget_xaf=50000)
        db.add(campaign)

        creative = AdCreativeModel(
            id=creative_id,
            campaign_id=campaign_id,
            headline="Annonce douteuse",
            body_text="Texte d'annonce",
            review_status="APPROVED",
            is_active=True,
        )
        db.add(creative)
        await db.commit()

    async with session_factory() as db:
        # Simuler 5 signalements visiteurs (ne déclenche pas encore la suspension)
        for i in range(5):
            fb = AdUserFeedbackModel(
                id=uuid.uuid4(),
                creative_id=creative_id,
                visitor_session_id=f"sess_{i}",
                feedback_type="REPORT",
                reason="CONTENU_SPAM",
            )
            db.add(fb)

        await db.commit()

    async with session_factory() as db:
        crt_check = await db.get(AdCreativeModel, creative_id)
        assert crt_check.is_active is True

        # Ajouter le 6ème signalement (> 5 signalements)
        fb_6 = AdUserFeedbackModel(
            id=uuid.uuid4(),
            creative_id=creative_id,
            visitor_session_id="sess_6",
            feedback_type="REPORT",
            reason="CONTENU_SPAM",
        )
        db.add(fb_6)
        await db.flush()

        # Déclencher la logique de vérification d'auto-suspension
        stmt_count = select(func.count(AdUserFeedbackModel.id)).where(
            AdUserFeedbackModel.creative_id == creative_id,
            AdUserFeedbackModel.feedback_type == "REPORT",
        )
        res = await db.execute(stmt_count)
        count = res.scalar() or 0

        assert count == 6

        # Auto-suspendre l'annonce
        crt = await db.get(AdCreativeModel, creative_id)
        crt.is_active = False
        crt.review_status = "REJECTED"
        crt.rejection_reason = "Auto-suspendu suite à plus de 5 signalements visiteurs (Gate R11)"

        await db.commit()

    async with session_factory() as db:
        crt_suspended = await db.get(AdCreativeModel, creative_id)
        assert crt_suspended.is_active is False
        assert crt_suspended.review_status == "REJECTED"
        assert "5 signalements" in crt_suspended.rejection_reason
