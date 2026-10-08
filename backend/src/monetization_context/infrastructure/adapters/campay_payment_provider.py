import hmac
import hashlib
import uuid
import httpx
from typing import Optional, Dict, Any

from monetization_context.domain.ports.payment_provider_port import (
    PaymentProviderPort,
    PaymentInitiationResult,
    PaymentVerificationResult,
    WebhookEventData,
)
from monetization_context.domain.value_objects import PaymentStatus, PaymentProviderName


class CampayProviderAdapter(PaymentProviderPort):
    """
    Adaptateur officiel pour l'agrégateur Campay (Cameroun Mobile Money - MTN MoMo & Orange Money).
    Documentation : https://demo.campay.net/api/
    """

    def __init__(
        self,
        app_username: str,
        app_password: str,
        webhook_secret: str,
        environment: str = "sandbox",  # sandbox or live
    ):
        self.app_username = app_username
        self.app_password = app_password
        self.webhook_secret = webhook_secret
        self.base_url = (
            "https://demo.campay.net/api" if environment.lower() == "sandbox" else "https://campay.net/api"
        )
        self._token: Optional[str] = None

    async def _get_access_token(self) -> str:
        """Obtient un jeton d'accès auprès de Campay API."""
        if self._token:
            return self._token

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/token/",
                json={"username": self.app_username, "password": self.app_password},
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["token"]
            return self._token

    async def initiate_payment(
        self,
        tenant_id: uuid.UUID,
        invoice_id: uuid.UUID,
        amount_xaf: int,
        phone_number: str,
        operator: str,
        description: str,
    ) -> PaymentInitiationResult:
        token = await self._get_access_token()
        # Format du numéro : s'assurer du préfixe 237 pour le Cameroun
        clean_phone = phone_number.replace("+", "").replace(" ", "")
        if not clean_phone.startswith("237") and len(clean_phone) == 9:
            clean_phone = f"237{clean_phone}"

        payload = {
            "amount": str(amount_xaf),
            "currency": "XAF",
            "from": clean_phone,
            "description": description,
            "external_reference": str(invoice_id),
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/collect/",
                json=payload,
                headers={"Authorization": f"Token {token}", "Content-Type": "application/json"},
            )
            
            if resp.status_code != 200:
                return PaymentInitiationResult(
                    provider_ref=f"ERR-{uuid.uuid4().hex[:8]}",
                    status=PaymentStatus.FAILED,
                    user_instructions="Erreur d'initialisation auprès de Campay",
                    raw_response=resp.json() if resp.headers.get("content-type") == "application/json" else {"text": resp.text},
                )

            data = resp.json()
            provider_ref = data.get("reference", str(uuid.uuid4()))
            raw_status = data.get("status", "PENDING").upper()

            if raw_status in ("SUCCESSFUL", "SUCCESS"):
                p_status = PaymentStatus.SUCCEEDED
            elif raw_status in ("FAILED", "REFUNDED"):
                p_status = PaymentStatus.FAILED
            else:
                p_status = PaymentStatus.PENDING

            ussd_code = data.get("ussd_code", "*126# (Orange) ou *123# (MTN)")

            return PaymentInitiationResult(
                provider_ref=provider_ref,
                status=p_status,
                user_instructions=f"Un prompt USSD a été envoyé au {phone_number}. Si besoin, composez {ussd_code}.",
                raw_response=data,
            )

    async def verify_payment_status(self, provider_ref: str) -> PaymentVerificationResult:
        token = await self._get_access_token()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/transaction/{provider_ref}/",
                headers={"Authorization": f"Token {token}"},
            )
            if resp.status_code != 200:
                return PaymentVerificationResult(
                    provider_ref=provider_ref,
                    status=PaymentStatus.FAILED,
                    amount_xaf=0,
                    raw_response={"error": resp.text},
                )
            data = resp.json()
            raw_status = data.get("status", "FAILED").upper()
            if raw_status in ("SUCCESSFUL", "SUCCESS"):
                p_status = PaymentStatus.SUCCEEDED
            elif raw_status == "PENDING":
                p_status = PaymentStatus.PENDING
            else:
                p_status = PaymentStatus.FAILED

            amount = int(float(data.get("amount", 0)))
            return PaymentVerificationResult(
                provider_ref=provider_ref,
                status=p_status,
                amount_xaf=amount,
                raw_response=data,
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
        raw_status = str(payload_dict.get("status", "FAILED")).upper()
        if raw_status in ("SUCCESSFUL", "SUCCESS", "PAID"):
            p_status = PaymentStatus.SUCCEEDED
        elif raw_status == "PENDING":
            p_status = PaymentStatus.PENDING
        else:
            p_status = PaymentStatus.FAILED

        amount_val = int(float(payload_dict.get("amount", 0)))

        return WebhookEventData(
            provider_name=PaymentProviderName.CAMPAY,
            provider_event_id=str(payload_dict.get("id", payload_dict.get("reference", uuid.uuid4().hex))),
            provider_ref=str(payload_dict.get("reference", "")),
            status=p_status,
            amount_xaf=amount_val,
            is_signature_valid=signature_valid,
            raw_payload=payload_dict,
        )
