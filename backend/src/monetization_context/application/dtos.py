# backend/src/monetization_context/application/dtos.py

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from monetization_context.domain.value_objects import (
    CampusLicenseTier,
    SponsorshipStatus,
    SubscriptionPlan,
)


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SponsorshipCreateDTO(BaseDTO):
    organization_id: UUID
    target_tenant_ids: List[UUID]
    budget_fcfa: int
    start_date: datetime
    end_date: datetime


class SponsorshipResponseDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    organization_id: UUID
    target_tenant_ids: List[UUID]
    budget_fcfa: int
    status: SponsorshipStatus
    start_date: datetime
    end_date: datetime


class LicenseStatusDTO(BaseDTO):
    tenant_id: UUID
    tier: CampusLicenseTier
    is_active: bool
    max_certified_students: int
    expires_at: datetime


class PlanDTO(BaseDTO):
    id: UUID
    code: str
    name: str
    price_xaf: int
    billing_period: str
    seats_included: int
    extra_seat_price_xaf: int
    features_json: dict
    is_active: bool


class InvoiceLineDTO(BaseDTO):
    id: UUID
    description: str
    quantity: int
    unit_price_xaf: int
    total_xaf: int


class InvoiceDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    number: str
    academic_year: str
    status: str
    subtotal_xaf: int
    tax_rate_percent: int
    tax_xaf: int
    total_xaf: int
    issue_date: datetime
    due_date: datetime
    paid_at: Optional[datetime] = None
    pdf_url: Optional[str] = None
    billing_contact_email: Optional[str] = None
    lines: List[InvoiceLineDTO] = []


class ManualPaymentProofDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    invoice_id: UUID
    file_path: str
    payment_reference: Optional[str] = None
    amount_declared_xaf: int
    status: str
    rejection_reason: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None


class PaymentAttemptDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    invoice_id: UUID
    amount_xaf: int
    channel: str
    provider_name: str
    provider_ref: Optional[str] = None
    phone_number_masked: Optional[str] = None
    status: str
    failure_reason: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class SubscriptionDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    plan_id: Optional[UUID] = None
    plan_code: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    auto_renew: bool = True
    cancel_at_period_end: bool = False
    trial_ends_at: Optional[datetime] = None
    grace_ends_at: Optional[datetime] = None
    billing_contact_email: Optional[str] = None
    seats_used: int = 0
    seats_included: int = 0


class ManualProofCreateDTO(BaseModel):
    invoice_id: UUID
    file_path: str
    amount_declared_xaf: int
    payment_reference: Optional[str] = None


class ManualProofReviewDTO(BaseModel):
    approve: bool
    rejection_reason: Optional[str] = None


class MobileMoneyPaymentDTO(BaseModel):
    invoice_id: UUID
    phone_number: str
    operator: str = "MTN"  # MTN or ORANGE


class ReconciliationAnomalyDTO(BaseDTO):
    attempt_id: UUID
    tenant_id: UUID
    invoice_id: UUID
    provider_name: str
    provider_ref: str
    db_status: str
    provider_status: str
    db_amount_xaf: int
    provider_amount_xaf: int
    anomaly_type: str
    details: str

