from abc import ABC, abstractmethod
from dataclasses import dataclass
import uuid
from typing import Optional, Dict, Any

from monetization_context.domain.value_objects import PaymentStatus

@dataclass
class PaymentInitiationResult:
    provider_ref: str
    status: PaymentStatus
    user_instructions: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None

@dataclass
class PaymentVerificationResult:
    provider_ref: str
    status: PaymentStatus
    amount_xaf: int
    raw_response: Optional[Dict[str, Any]] = None

@dataclass
class WebhookEventData:
    provider_name: str
    provider_event_id: str
    provider_ref: str
    status: PaymentStatus
    amount_xaf: int
    is_signature_valid: bool
    raw_payload: Dict[str, Any]

class PaymentProviderPort(ABC):
    """Port hexagonal pour les fournisseurs de paiement (Campay Mobile Money, FakeProvider, etc.)."""

    @abstractmethod
    async def initiate_payment(
        self,
        tenant_id: uuid.UUID,
        invoice_id: uuid.UUID,
        amount_xaf: int,
        phone_number: str,
        operator: str,  # MTN, ORANGE
        description: str,
    ) -> PaymentInitiationResult:
        pass

    @abstractmethod
    async def verify_payment_status(self, provider_ref: str) -> PaymentVerificationResult:
        pass

    @abstractmethod
    def verify_webhook_signature(
        self, payload_bytes: bytes, signature_header: Optional[str], secret: str
    ) -> bool:
        pass

    @abstractmethod
    def parse_webhook_event(self, payload_dict: Dict[str, Any], signature_valid: bool) -> WebhookEventData:
        pass
