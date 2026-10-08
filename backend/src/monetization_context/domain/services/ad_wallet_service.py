# backend/src/monetization_context/domain/services/ad_wallet_service.py

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from monetization_context.infrastructure.persistence.models import AdWalletModel, WalletTransactionModel

logger = logging.getLogger("AdWalletService")


class AdWalletService:
    """
    Service du portefeuille prépayé annonceur (AdWallet).
    Gère les crédits, les débits atomiques de diffusion et l'assertion d'intégrité du journal.
    Toutes les sommes sont en entiers XAF (FCFA).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_wallet(self, advertiser_id: uuid.UUID) -> AdWalletModel:
        """Récupère le portefeuille d'un annonceur ou le crée avec un solde initial de 0 FCFA."""
        stmt = select(AdWalletModel).where(AdWalletModel.advertiser_id == advertiser_id)
        res = await self.db.execute(stmt)
        wallet = res.scalars().first()

        if not wallet:
            wallet = AdWalletModel(
                id=uuid.uuid4(),
                advertiser_id=advertiser_id,
                balance_xaf=0,
            )
            self.db.add(wallet)
            await self.db.flush()

        return wallet

    async def credit_wallet(
        self,
        wallet_id: uuid.UUID,
        amount_xaf: int,
        reference_id: Optional[str] = None,
        description: str = "Dépôt de solde prépayé",
        transaction_type: str = "DEPOSIT",
    ) -> WalletTransactionModel:
        """
        Crédite le portefeuille d'un montant XAF positif.
        Incrémente le solde et consigne une entrée immuable dans le journal.
        """
        if amount_xaf <= 0:
            raise ValueError("Le montant à créditer doit être strictement positif (> 0 FCFA).")

        wallet = await self.db.get(AdWalletModel, wallet_id)
        if not wallet:
            raise ValueError(f"Portefeuille {wallet_id} introuvable.")

        wallet.balance_xaf += amount_xaf
        wallet.updated_at = datetime.now(timezone.utc)

        tx = WalletTransactionModel(
            id=uuid.uuid4(),
            wallet_id=wallet_id,
            type=transaction_type,
            amount_xaf=amount_xaf,
            balance_after_xaf=wallet.balance_xaf,
            reference_id=reference_id,
            description=description,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(tx)
        await self.db.flush()
        logger.info(f"Portefeuille {wallet_id} crédité de {amount_xaf} XAF (Nouveau solde: {wallet.balance_xaf} XAF)")
        return tx

    async def debit_wallet_for_delivery(
        self,
        wallet_id: uuid.UUID,
        amount_xaf: int,
        reference_id: Optional[str] = None,
        description: str = "Débit de diffusion publicitaire",
    ) -> Tuple[bool, Optional[WalletTransactionModel], str]:
        """
        Débite atomiquement le portefeuille pour une impression ou un clic.
        Retourne (True, transaction, "SUCCESS") ou (False, None, "INSUFFICIENT_FUNDS").
        """
        if amount_xaf <= 0:
            raise ValueError("Le montant à débiter doit être strictement positif.")

        wallet = await self.db.get(AdWalletModel, wallet_id)
        if not wallet:
            return False, None, "WALLET_NOT_FOUND"

        if wallet.balance_xaf < amount_xaf:
            return False, None, "INSUFFICIENT_FUNDS"

        # Débit atomique
        wallet.balance_xaf -= amount_xaf
        wallet.updated_at = datetime.now(timezone.utc)

        tx = WalletTransactionModel(
            id=uuid.uuid4(),
            wallet_id=wallet_id,
            type="AD_DELIVERY_DEBIT",
            amount_xaf=-amount_xaf,
            balance_after_xaf=wallet.balance_xaf,
            reference_id=reference_id,
            description=description,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(tx)
        await self.db.flush()
        return True, tx, "SUCCESS"

    async def refund_wallet(
        self,
        wallet_id: uuid.UUID,
        amount_xaf: int,
        reference_id: Optional[str] = None,
        description: str = "Remboursement / Ajustement solde",
    ) -> WalletTransactionModel:
        """Rembourse ou crédite un montant d'ajustement au portefeuille."""
        return await self.credit_wallet(
            wallet_id=wallet_id,
            amount_xaf=amount_xaf,
            reference_id=reference_id,
            description=description,
            transaction_type="REFUND",
        )

    async def assert_balance_integrity(self, wallet_id: uuid.UUID) -> bool:
        """
        Vérifie l'intégrité du journal comptable immuable :
        solde_actuel == somme(amount_xaf de toutes les transactions).
        """
        wallet = await self.db.get(AdWalletModel, wallet_id)
        if not wallet:
            return False

        sum_stmt = select(func.coalesce(func.sum(WalletTransactionModel.amount_xaf), 0)).where(
            WalletTransactionModel.wallet_id == wallet_id
        )
        res = await self.db.execute(sum_stmt)
        journal_sum = res.scalar_one()

        is_valid = (wallet.balance_xaf == journal_sum)
        if not is_valid:
            logger.error(f"ATTENTION: Incohérence journal portefeuille {wallet_id}: solde={wallet.balance_xaf}, somme_journal={journal_sum}")
        return is_valid
