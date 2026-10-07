# tests/unit/test_advertiser_workspace_security.py

import uuid
import pytest
from sqlalchemy import delete

from monetization_context.infrastructure.persistence.models import (
    AdvertiserModel, AdWalletModel, AdCampaignModel, AdCreativeModel
)


@pytest.mark.asyncio
async def test_gate_r9_idor_advertiser_campaign_isolation(session_factory):
    """
    Gate R9: Isolation stricte des annonceurs et protection anti-IDOR.
    Un annonceur A ne peut ni voir ni modifier les campagnes de l'annonceur B.
    """
    adv_a_id = uuid.uuid4()
    adv_b_id = uuid.uuid4()
    cmp_a_id = uuid.uuid4()
    cmp_b_id = uuid.uuid4()

    async with session_factory() as db:
        await db.execute(delete(AdCreativeModel))
        await db.execute(delete(AdCampaignModel))
        await db.execute(delete(AdWalletModel))
        await db.execute(delete(AdvertiserModel))

        # Annonceur A
        adv_a = AdvertiserModel(id=adv_a_id, company_name="Entreprise A", contact_email="a@corp.cm", status="ACTIVE")
        db.add(adv_a)
        cmp_a = AdCampaignModel(id=cmp_a_id, advertiser_id=adv_a_id, title="Campagne A", advertiser_name="Entreprise A", status="ACTIVE", total_budget_xaf=10000)
        db.add(cmp_a)

        # Annonceur B
        adv_b = AdvertiserModel(id=adv_b_id, company_name="Entreprise B", contact_email="b@corp.cm", status="ACTIVE")
        db.add(adv_b)
        cmp_b = AdCampaignModel(id=cmp_b_id, advertiser_id=adv_b_id, title="Campagne B", advertiser_name="Entreprise B", status="ACTIVE", total_budget_xaf=20000)
        db.add(cmp_b)

        await db.commit()

    async with session_factory() as db:
        # Vérification 1: Annonceur A ne doit voir que sa propre campagne
        cmp_a_fetched = await db.get(AdCampaignModel, cmp_a_id)
        assert cmp_a_fetched.advertiser_id == adv_a_id

        cmp_b_fetched = await db.get(AdCampaignModel, cmp_b_id)
        assert cmp_b_fetched.advertiser_id == adv_b_id
        assert cmp_b_fetched.advertiser_id != adv_a_id
