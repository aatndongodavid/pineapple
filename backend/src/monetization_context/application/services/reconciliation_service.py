# backend/src/monetization_context/application/services/reconciliation_service.py

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from monetization_context.domain.ports.payment_provider_port import PaymentProviderPort
from monetization_context.domain.value_objects import (
    InvoiceStatus,
    PaymentStatus,
    SubscriptionStatus,
)
from monetization_context.infrastructure.persistence.models import (
    InvoiceModel,
    PaymentModel,
    PaymentAttemptModel,
)
from identity_context.infrastructure.persistence.models import TenantSubscriptionModel
from monetization_context.application.dtos import ReconciliationAnomalyDTO

logger = logging.getLogger(__name__)


class ReconciliationService:
    """
    Service de réconciliation périodique des paiements entre la base de données et l'agrégateur (Campay/Fake).
    Détecte les écarts (statut, montant) et met à jour automatiquement les paiements en attente (Gate B4).
    """

    def __init__(self, session: AsyncSession, payment_provider: Optional[PaymentProviderPort] = None):
        self.session = session
        self.provider = payment_provider

    async def reconcile_pending_attempts(self) -> List[ReconciliationAnomalyDTO]:
        """
        Scanne les tentatives de paiement PENDING et vérifie leur statut réel auprès de l'agrégateur.
        Retourne la liste des anomalies détectées (écarts de montant, incohérences de statut, etc.).
        """
        if not self.provider:
            logger.warning("ReconciliationService execute sans fournisseur de paiement configuré")
            return []

        # Sélectionner les tentatives en PENDING (ou récentes)
        stmt = select(PaymentAttemptModel).where(PaymentAttemptModel.status == PaymentStatus.PENDING)
        res = await self.session.execute(stmt)
        pending_attempts = res.scalars().all()

        anomalies: List[ReconciliationAnomalyDTO] = []
        now = datetime.now(timezone.utc)

        for attempt in pending_attempts:
            if not attempt.provider_ref:
                continue

            try:
                verification = await self.provider.verify_payment_status(attempt.provider_ref)
            except Exception as exc:
                logger.error(f"Erreur lors de la vérification provider_ref={attempt.provider_ref}: {exc}")
                anomalies.append(
                    ReconciliationAnomalyDTO(
                        attempt_id=attempt.id,
                        tenant_id=attempt.tenant_id,
                        invoice_id=attempt.invoice_id,
                        provider_name=attempt.provider_name,
                        provider_ref=attempt.provider_ref,
                        db_status=attempt.status,
                        provider_status="ERROR",
                        db_amount_xaf=attempt.amount_xaf,
                        provider_amount_xaf=0,
                        anomaly_type="PROVIDER_ERROR",
                        details=f"Impossible de contacter l'agrégateur: {str(exc)}",
                    )
                )
                continue

            # Cas 1 : L'agrégateur confirme le succès
            if verification.status == PaymentStatus.SUCCEEDED:
                # Vérifier si le montant correspond
                if verification.amount_xaf > 0 and verification.amount_xaf != attempt.amount_xaf:
                    anomalies.append(
                        ReconciliationAnomalyDTO(
                            attempt_id=attempt.id,
                            tenant_id=attempt.tenant_id,
                            invoice_id=attempt.invoice_id,
                            provider_name=attempt.provider_name,
                            provider_ref=attempt.provider_ref,
                            db_status=attempt.status,
                            provider_status=verification.status,
                            db_amount_xaf=attempt.amount_xaf,
                            provider_amount_xaf=verification.amount_xaf,
                            anomaly_type="AMOUNT_MISMATCH",
                            details=f"Montant payé ({verification.amount_xaf} XAF) != Montant facture ({attempt.amount_xaf} XAF)",
                        )
                    )

                # Réconcilier le statut PENDING -> SUCCEEDED dans la DB
                attempt.status = PaymentStatus.SUCCEEDED
                attempt.completed_at = now

                # Marquer la facture comme payée si ce n'est pas déjà fait
                inv_stmt = select(InvoiceModel).where(InvoiceModel.id == attempt.invoice_id)
                inv_res = await self.session.execute(inv_stmt)
                invoice = inv_res.scalar_one_or_none()

                if invoice and invoice.status != InvoiceStatus.PAID:
                    invoice.status = InvoiceStatus.PAID
                    invoice.paid_at = now

                    pmt = PaymentModel(
                        id=uuid.uuid4(),
                        tenant_id=attempt.tenant_id,
                        invoice_id=invoice.id,
                        amount_xaf=verification.amount_xaf or attempt.amount_xaf,
                        currency="XAF",
                        channel=attempt.channel,
                        provider_name=attempt.provider_name,
                        provider_ref=attempt.provider_ref,
                        status=PaymentStatus.SUCCEEDED,
                        paid_at=now,
                    )
                    self.session.add(pmt)

                    # Prolonger l'abonnement du tenant
                    await self._extend_tenant_subscription(attempt.tenant_id, now)

            # Cas 2 : L'agrégateur confirme l'échec
            elif verification.status == PaymentStatus.FAILED:
                attempt.status = PaymentStatus.FAILED

            # Cas 3 : Toujours PENDING chez l'agrégateur (pas d'action, statut inchangé)

        await self.session.commit()
        return anomalies

    async def scan_all_anomalies(self) -> List[ReconciliationAnomalyDTO]:
        """
        Inspecte l'intégralité des paiements réussis et en attente pour détecter des incohérences.
        """
        if not self.provider:
            return []

        stmt = select(PaymentAttemptModel)
        res = await self.session.execute(stmt)
        all_attempts = res.scalars().all()

        anomalies: List[ReconciliationAnomalyDTO] = []
        for attempt in all_attempts:
            if not attempt.provider_ref or attempt.provider_name == "MANUAL_WIRE":
                continue

            try:
                verification = await self.provider.verify_payment_status(attempt.provider_ref)
            except Exception:
                continue

            if attempt.status == PaymentStatus.SUCCEEDED and verification.status != PaymentStatus.SUCCEEDED:
                anomalies.append(
                    ReconciliationAnomalyDTO(
                        attempt_id=attempt.id,
                        tenant_id=attempt.tenant_id,
                        invoice_id=attempt.invoice_id,
                        provider_name=attempt.provider_name,
                        provider_ref=attempt.provider_ref,
                        db_status=attempt.status,
                        provider_status=verification.status,
                        db_amount_xaf=attempt.amount_xaf,
                        provider_amount_xaf=verification.amount_xaf,
                        anomaly_type="STATUS_MISMATCH",
                        details=f"DB indique SUCCEEDED mais l'agrégateur indique {verification.status}",
                    )
                )

        return anomalies

    async def _extend_tenant_subscription(self, tenant_id: uuid.UUID, payment_time: datetime):
        sub_stmt = select(TenantSubscriptionModel).where(TenantSubscriptionModel.tenant_id == tenant_id)
        sub_res = await self.session.execute(sub_stmt)
        subscription = sub_res.scalar_one_or_none()

        if not subscription:
            subscription = TenantSubscriptionModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                plan="STANDARD",
                status=SubscriptionStatus.ACTIVE,
                current_period_start=payment_time,
                current_period_end=payment_time + timedelta(days=365),
                starts_at=payment_time,
                ends_at=payment_time + timedelta(days=365),
            )
            self.session.add(subscription)
        else:
            subscription.status = SubscriptionStatus.ACTIVE
            current_end = subscription.current_period_end
            if current_end and current_end.tzinfo is None:
                current_end = current_end.replace(tzinfo=timezone.utc)

            payment_time_utc = payment_time if payment_time.tzinfo else payment_time.replace(tzinfo=timezone.utc)

            if current_end and current_end > payment_time_utc:
                new_end = current_end + timedelta(days=365)
                subscription.current_period_end = new_end
                subscription.ends_at = new_end
            else:
                subscription.current_period_start = payment_time_utc
                subscription.starts_at = payment_time_utc
                new_end = payment_time_utc + timedelta(days=365)
                subscription.current_period_end = new_end
                subscription.ends_at = new_end
