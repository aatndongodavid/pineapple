import hmac
import hashlib
import uuid
from typing import Optional, Dict, Any

from monetization_context.domain.ports.payment_provider_port import (
    PaymentProviderPort,
    PaymentInitiationResult,
    PaymentVerificationResult,
    WebhookEventData,
)
from monetization_context.domain.value_objects import PaymentStatus, PaymentProviderName

class FakePaymentProviderAdapter(PaymentProviderPort):
    """Adaptateur de test / démo pour le fournisseur de paiement simulé."""

    def __init__(self, webhook_secret: str = "fake_webhook_secret_key"):
        self.webhook_secret = webhook_secret
        self.transactions: Dict[str, Dict[str, Any]] = {}

    async def initiate_payment(
        self,
        tenant_id: uuid.UUID,
        invoice_id: uuid.UUID,
        amount_xaf: int,
        phone_number: str,
        operator: str,
        description: str,
    ) -> PaymentInitiationResult:
        provider_ref = f"FAKE-{uuid.uuid4().hex[:12].upper()}"

        # Simulation selon le numéro de téléphone
        if phone_number.endswith("0000") or phone_number.endswith("690000000"):
            status = PaymentStatus.SUCCEEDED
            instructions = "Paiement réussi instantanément (Mode Démo)"
        elif phone_number.endswith("9999") or phone_number.endswith("670000000"):
            status = PaymentStatus.FAILED
            instructions = "Échec du paiement (Numéro de test d'échec)"
        else:
            status = PaymentStatus.PENDING
            instructions = "Veuillez valider le USSD push sur votre téléphone"

        tx_info = {
            "provider_ref": provider_ref,
            "tenant_id": str(tenant_id),
            "invoice_id": str(invoice_id),
            "amount_xaf": amount_xaf,
            "status": status,
            "phone_number": phone_number,
            "operator": operator,
        }
        self.transactions[provider_ref] = tx_info

        return PaymentInitiationResult(
            provider_ref=provider_ref,
            status=status,
            user_instructions=instructions,
            raw_response=tx_info,
        )

    async def verify_payment_status(self, provider_ref: str) -> PaymentVerificationResult:
        tx = self.transactions.get(provider_ref)
        if not tx:
            return PaymentVerificationResult(
                provider_ref=provider_ref,
                status=PaymentStatus.FAILED,
                amount_xaf=0,
                raw_response={"error": "Transaction not found"},
            )
        return PaymentVerificationResult(
            provider_ref=provider_ref,
            status=tx["status"],
            amount_xaf=tx["amount_xaf"],
            raw_response=tx,
        )

    def verify_webhook_signature(
        self, payload_bytes: bytes, signature_header: Optional[str], secret: str
    ) -> bool:
        if not signature_header:
            return False
        expected_sig = hmac.new(
            secret.encode("utf-8"), payload_bytes, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_sig, signature_header)

    def parse_webhook_event(self, payload_dict: Dict[str, Any], signature_valid: bool) -> WebhookEventData:
        status_str = payload_dict.get("status", "FAILED").upper()
        if status_str in ("SUCCESS", "SUCCEEDED", "PAID"):
            p_status = PaymentStatus.SUCCEEDED
        elif status_str in ("PENDING", "PROCESSING"):
            p_status = PaymentStatus.PENDING
        else:
            p_status = PaymentStatus.FAILED

        return WebhookEventData(
            provider_name=PaymentProviderName.FAKE,
            provider_event_id=payload_dict.get("event_id", f"evt_{uuid.uuid4().hex[:8]}"),
            provider_ref=payload_dict.get("reference", payload_dict.get("provider_ref", "")),
            status=p_status,
            amount_xaf=int(payload_dict.get("amount", 0)),
            is_signature_valid=signature_valid,
            raw_payload=payload_dict,
        )
