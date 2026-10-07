import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from monetization_context.domain.ports.payment_provider_port import PaymentProviderPort, WebhookEventData
from monetization_context.domain.value_objects import (
    InvoiceStatus,
    PaymentStatus,
    ManualProofStatus,
    SubscriptionStatus,
    BillingPeriod,
)
from monetization_context.infrastructure.persistence.models import (
    InvoiceModel,
    PaymentModel,
    PaymentAttemptModel,
    PaymentEventModel,
    ManualPaymentProofModel,
    PlanModel,
)
from identity_context.infrastructure.persistence.models import TenantSubscriptionModel
from monetization_context.application.dtos import ManualPaymentProofDTO, PaymentAttemptDTO


class PaymentApplicationService:
    """Service d'application d'encaissement, validation des preuves manuelles et webhooks idempotents."""

    def __init__(self, session: AsyncSession, payment_provider: Optional[PaymentProviderPort] = None):
        self.session = session
        self.provider = payment_provider

    async def submit_manual_proof(
        self,
        tenant_id: uuid.UUID,
        invoice_id: uuid.UUID,
        file_path: str,
        amount_declared_xaf: int,
        payment_reference: Optional[str] = None,
    ) -> ManualPaymentProofDTO:
        # Vérifier que la facture existe et appartient bien au tenant
        invoice_stmt = select(InvoiceModel).where(
            InvoiceModel.id == invoice_id, InvoiceModel.tenant_id == tenant_id
        )
        invoice_res = await self.session.execute(invoice_stmt)
        invoice = invoice_res.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facture introuvable pour cet établissement")

        proof = ManualPaymentProofModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            file_path=file_path,
            payment_reference=payment_reference,
            amount_declared_xaf=amount_declared_xaf,
            status=ManualProofStatus.SUBMITTED,
        )
        self.session.add(proof)
        await self.session.commit()

        return self._map_proof_dto(proof)

    async def review_manual_proof(
        self,
        proof_id: uuid.UUID,
        reviewer_user_id: uuid.UUID,
        approve: bool,
        rejection_reason: Optional[str] = None,
    ) -> ManualPaymentProofDTO:
        proof_stmt = select(ManualPaymentProofModel).where(ManualPaymentProofModel.id == proof_id)
        proof_res = await self.session.execute(proof_stmt)
        proof = proof_res.scalar_one_or_none()
        if not proof:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preuve de paiement introuvable")

        if proof.status != ManualProofStatus.SUBMITTED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cette preuve a déjà été traitée")

        now = datetime.now(timezone.utc)
        proof.reviewed_by_user_id = reviewer_user_id
        proof.reviewed_at = now

        if approve:
            proof.status = ManualProofStatus.APPROVED

            # Valider et marquer la facture payée
            inv_stmt = select(InvoiceModel).where(InvoiceModel.id == proof.invoice_id)
            inv_res = await self.session.execute(inv_stmt)
            invoice = inv_res.scalar_one_or_none()
            if invoice and invoice.status != InvoiceStatus.PAID:
                invoice.status = InvoiceStatus.PAID
                invoice.paid_at = now

                # Enregistrer le paiement
                pmt = PaymentModel(
                    id=uuid.uuid4(),
                    tenant_id=proof.tenant_id,
                    invoice_id=invoice.id,
                    amount_xaf=proof.amount_declared_xaf,
                    currency="XAF",
                    channel="MANUAL",
                    provider_name="MANUAL_WIRE",
                    provider_ref=proof.payment_reference or str(proof.id),
                    status=PaymentStatus.SUCCEEDED,
                    paid_at=now,
                )
                self.session.add(pmt)

                # Prolonger l'abonnement du tenant de manière idempotente
                await self._extend_tenant_subscription(proof.tenant_id, now)

        else:
            if not rejection_reason:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Un motif de rejet est obligatoire")
            proof.status = ManualProofStatus.REJECTED
            proof.rejection_reason = rejection_reason

        await self.session.commit()
        return self._map_proof_dto(proof)

    async def initiate_mobile_money_payment(
        self,
        tenant_id: uuid.UUID,
        invoice_id: uuid.UUID,
        phone_number: str,
        operator: str,
    ) -> PaymentAttemptDTO:
        if not self.provider:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fournisseur de paiement non configuré")

        inv_stmt = select(InvoiceModel).where(InvoiceModel.id == invoice_id, InvoiceModel.tenant_id == tenant_id)
        inv_res = await self.session.execute(inv_stmt)
        invoice = inv_res.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facture introuvable")

        if invoice.status == InvoiceStatus.PAID:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cette facture est déjà payée")

        init_result = await self.provider.initiate_payment(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            amount_xaf=invoice.total_xaf,
            phone_number=phone_number,
            operator=operator,
            description=f"Paiement facture {invoice.number}",
        )

        masked_phone = f"{phone_number[:3]}***{phone_number[-2:]}" if len(phone_number) >= 5 else phone_number

        attempt = PaymentAttemptModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            amount_xaf=invoice.total_xaf,
            channel="MOBILE_MONEY",
            provider_name="CAMPAY",
            provider_ref=init_result.provider_ref,
            phone_number_masked=masked_phone,
            status=init_result.status,
            completed_at=datetime.now(timezone.utc) if init_result.status == PaymentStatus.SUCCEEDED else None,
        )
        self.session.add(attempt)

        if init_result.status == PaymentStatus.SUCCEEDED:
            now = datetime.now(timezone.utc)
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = now
            pmt = PaymentModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                invoice_id=invoice.id,
                amount_xaf=invoice.total_xaf,
                currency="XAF",
                channel="MOBILE_MONEY",
                provider_name="CAMPAY",
                provider_ref=init_result.provider_ref,
                status=PaymentStatus.SUCCEEDED,
                paid_at=now,
            )
            self.session.add(pmt)
            await self._extend_tenant_subscription(tenant_id, now)

        await self.session.commit()
        return self._map_attempt_dto(attempt)

    async def process_webhook_payload(
        self,
        provider_name: str,
        payload_bytes: bytes,
        signature_header: Optional[str],
        secret: str,
    ) -> Dict[str, Any]:
        """Traitement idempotent et sécurisé d'un webhook de paiement (B1, B2, B3)."""
        is_sig_valid = False
        if self.provider:
            is_sig_valid = self.provider.verify_webhook_signature(payload_bytes, signature_header, secret)

        if not is_sig_valid:
            # Enregistrer la tentative de signature invalide (B3)
            evt_invalid = PaymentEventModel(
                id=uuid.uuid4(),
                provider_name=provider_name,
                provider_event_id=f"invalid_sig_{uuid.uuid4().hex[:8]}",
                payload_json=payload_bytes.decode("utf-8", errors="ignore"),
                is_signature_valid=False,
            )
            self.session.add(evt_invalid)
            await self.session.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Signature du webhook invalide ou rejetée")

        try:
            payload_dict = json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=400, detail="Payload JSON invalide")

        event_data: WebhookEventData = self.provider.parse_webhook_event(payload_dict, signature_valid=True)

        # Vérifier l'idempotence (B2) : Si provider_event_id a déjà été traité
        evt_stmt = select(PaymentEventModel).where(
            PaymentEventModel.provider_name == provider_name,
            PaymentEventModel.provider_event_id == event_data.provider_event_id,
        )
        evt_res = await self.session.execute(evt_stmt)
        existing_event = evt_res.scalar_one_or_none()

        if existing_event and existing_event.processed_at is not None:
            # Déjà traité ! Retourner succès immédiatement sans ré-appliquer les effets
            return {"status": "already_processed", "event_id": event_data.provider_event_id}

        now = datetime.now(timezone.utc)

        if not existing_event:
            event_model = PaymentEventModel(
                id=uuid.uuid4(),
                provider_name=provider_name,
                provider_event_id=event_data.provider_event_id,
                payload_json=json.dumps(payload_dict),
                is_signature_valid=True,
                processed_at=now,
            )
            self.session.add(event_model)
        else:
            existing_event.processed_at = now

        # Retrouver la tentative de paiement ou la facture correspondante
        att_stmt = select(PaymentAttemptModel).where(PaymentAttemptModel.provider_ref == event_data.provider_ref)
        att_res = await self.session.execute(att_stmt)
        attempt = att_res.scalar_one_or_none()

        if attempt:
            attempt.status = event_data.status
            if event_data.status == PaymentStatus.SUCCEEDED:
                attempt.completed_at = now

                # Marquer la facture comme payée
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
                        amount_xaf=event_data.amount_xaf or invoice.total_xaf,
                        currency="XAF",
                        channel="MOBILE_MONEY",
                        provider_name=provider_name,
                        provider_ref=event_data.provider_ref,
                        status=PaymentStatus.SUCCEEDED,
                        paid_at=now,
                    )
                    self.session.add(pmt)

                    # Prolonger l'abonnement du tenant de manière idempotente (B1)
                    await self._extend_tenant_subscription(attempt.tenant_id, now)

        await self.session.commit()
        return {"status": "success", "event_id": event_data.provider_event_id}

    async def _extend_tenant_subscription(self, tenant_id: uuid.UUID, payment_time: datetime):
        """Active ou prolonge l'abonnement d'un établissement d'une période académique exacte."""
        sub_stmt = select(TenantSubscriptionModel).where(TenantSubscriptionModel.tenant_id == tenant_id)
        sub_res = await self.session.execute(sub_stmt)
        subscription = sub_res.scalar_one_or_none()

        if not subscription:
            # Créer un abonnement standard par défaut
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
                # Prolonger la fin de période existante de 365 jours
                new_end = current_end + timedelta(days=365)
                subscription.current_period_end = new_end
                subscription.ends_at = new_end
            else:
                subscription.current_period_start = payment_time_utc
                subscription.starts_at = payment_time_utc
                new_end = payment_time_utc + timedelta(days=365)
                subscription.current_period_end = new_end
                subscription.ends_at = new_end

    def _map_proof_dto(self, proof: ManualPaymentProofModel) -> ManualPaymentProofDTO:
        return ManualPaymentProofDTO(
            id=proof.id,
            tenant_id=proof.tenant_id,
            invoice_id=proof.invoice_id,
            file_path=proof.file_path,
            payment_reference=proof.payment_reference,
            amount_declared_xaf=proof.amount_declared_xaf,
            status=proof.status,
            rejection_reason=proof.rejection_reason,
            submitted_at=proof.submitted_at,
            reviewed_at=proof.reviewed_at,
        )

    def _map_attempt_dto(self, attempt: PaymentAttemptModel) -> PaymentAttemptDTO:
        return PaymentAttemptDTO(
            id=attempt.id,
            tenant_id=attempt.tenant_id,
            invoice_id=attempt.invoice_id,
            amount_xaf=attempt.amount_xaf,
            channel=attempt.channel,
            provider_name=attempt.provider_name,
            provider_ref=attempt.provider_ref,
            phone_number_masked=attempt.phone_number_masked,
            status=attempt.status,
            failure_reason=attempt.failure_reason,
            created_at=attempt.created_at,
            completed_at=attempt.completed_at,
        )
