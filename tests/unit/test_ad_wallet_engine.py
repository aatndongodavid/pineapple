# tests/unit/test_ad_wallet_engine.py

import uuid
import pytest
from sqlalchemy import select

from monetization_context.infrastructure.persistence.models import AdvertiserModel, AdWalletModel, WalletTransactionModel
from monetization_context.domain.services.ad_wallet_service import AdWalletService


@pytest.mark.asyncio
async def test_gate_r10_wallet_creation_and_deposit(session_factory):
    """
    Gate R10: Création du portefeuille et dépôt initial.
    Vérifie l'écriture dans le journal et la mise à jour du solde.
    """
    advertiser_id = uuid.uuid4()
    async with session_factory() as db:
        advertiser = AdvertiserModel(
            id=advertiser_id,
            company_name="Société Pub Test",
            contact_email="pub@test.com",
            country="CM",
            status="ACTIVE",
        )
        db.add(advertiser)
        await db.commit()

    async with session_factory() as db:
        service = AdWalletService(db)
        wallet = await service.get_or_create_wallet(advertiser_id)
        assert wallet.balance_xaf == 0

        # Créditer de 50 000 FCFA
        tx = await service.credit_wallet(wallet.id, 50000, reference_id="REF_PAY_001", description="Dépôt Mobile Money")
        assert tx.amount_xaf == 50000
        assert tx.balance_after_xaf == 50000
        await db.commit()

    # Vérification persistance DB
    async with session_factory() as db:
        service = AdWalletService(db)
        is_integral = await service.assert_balance_integrity(wallet.id)
        assert is_integral is True


@pytest.mark.asyncio
async def test_gate_r10_wallet_debit_and_insufficient_funds(session_factory):
    """
    Gate R10: Débit atomique de diffusion et rejet si solde insuffisant.
    Le solde ne doit jamais devenir négatif.
    """
    advertiser_id = uuid.uuid4()
    async with session_factory() as db:
        advertiser = AdvertiserModel(
            id=advertiser_id,
            company_name="Annonceur Restreint",
            contact_email="restreint@test.com",
            country="CM",
            status="ACTIVE",
        )
        db.add(advertiser)
        await db.commit()

    async with session_factory() as db:
        service = AdWalletService(db)
        wallet = await service.get_or_create_wallet(advertiser_id)
        # Créditer de 1 000 FCFA
        await service.credit_wallet(wallet.id, 1000, reference_id="REF_002", description="Petit crédit")
        await db.commit()

    # 1. Débit valide de 600 FCFA
    async with session_factory() as db:
        service = AdWalletService(db)
        success, tx, reason = await service.debit_wallet_for_delivery(wallet.id, 600, description="Impression 600 FCFA")
        assert success is True
        assert reason == "SUCCESS"
        assert tx.amount_xaf == -600
        assert tx.balance_after_xaf == 400
        await db.commit()

    # 2. Débit excessif de 500 FCFA (solde disponible: 400 FCFA) -> Rejet
    async with session_factory() as db:
        service = AdWalletService(db)
        success2, tx2, reason2 = await service.debit_wallet_for_delivery(wallet.id, 500, description="Impression trop chère")
        assert success2 is False
        assert reason2 == "INSUFFICIENT_FUNDS"
        assert tx2 is None

    # 3. Vérification de l'intégrité du journal comptable immuable
    async with session_factory() as db:
        service = AdWalletService(db)
        wallet_db = await db.get(AdWalletModel, wallet.id)
        assert wallet_db.balance_xaf == 400
        is_integral = await service.assert_balance_integrity(wallet.id)
        assert is_integral is True
