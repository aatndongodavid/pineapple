# backend/src/monetization_context/infrastructure/persistence/models.py

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from monetization_context.domain.value_objects import (
    BillingPeriod,
    CampusLicenseTier,
    DunningEventType,
    InvoiceStatus,
    ManualProofStatus,
    PaymentChannel,
    PaymentProviderName,
    PaymentStatus,
    SponsorshipStatus,
    SubscriptionStatus,
)
from shared_kernel.infrastructure.database import Base


class PlanModel(Base):
    """Catalogue des forfaits d'abonnement (modifiable par le super-admin)."""
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)  # En entiers FCFA
    billing_period: Mapped[str] = mapped_column(String(50), default="ACADEMIC_YEAR", nullable=False)
    seats_included: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    extra_seat_price_xaf: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    trial_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    features_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class InvoiceModel(Base):
    """Factures d'abonnement avec numérotation séquentielle sans trou par tenant et par an."""
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "number", name="uq_invoice_number_per_tenant"),
        Index("idx_invoice_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    number: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # ex: FAC-2027-ENSPD-0001
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", nullable=False)  # DRAFT, ISSUED, PAID, VOID, OVERDUE

    subtotal_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tax_rate_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # ex: 0 ou 19 pour TVA
    tax_xaf: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)

    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    billing_contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class InvoiceLineModel(Base):
    """Lignes de détail d'une facture."""
    __tablename__ = "invoice_lines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)


class PaymentModel(Base):
    """Paiements enregistrés (Mobile Money, Manuel, Avoir)."""
    __tablename__ = "payments"
    __table_args__ = (
        Index("idx_payment_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # MOBILE_MONEY, MANUAL_PROOF, CREDIT_NOTE, SUPER_ADMIN
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)  # CAMPAY, NOTCHPAY, MANUAL, FAKE
    provider_ref: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)

    amount_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="XAF", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, SUCCEEDED, FAILED, REFUNDED
    phone_number_masked: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PaymentAttemptModel(Base):
    """Tentatives individuelles d'encaissement."""
    __tablename__ = "payment_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"), index=True, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    response_payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PaymentEventModel(Base):
    """Événements de Webhook récepteurs idempotents."""
    __tablename__ = "payment_events"
    __table_args__ = (
        UniqueConstraint("provider_name", "provider_event_id", name="uq_payment_event_provider_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    is_signature_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ManualPaymentProofModel(Base):
    """Preuves de paiement manuel téléversées par les établissements (virement / espèces)."""
    __tablename__ = "manual_payment_proofs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount_declared_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SUBMITTED", nullable=False)  # SUBMITTED, APPROVED, REJECTED
    reviewed_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CreditNoteModel(Base):
    """Avoirs et remboursements émis."""
    __tablename__ = "credit_notes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    amount_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class DunningEventModel(Base):
    """Historique des relances de paiement (Dunning)."""
    __tablename__ = "dunning_events"
    __table_args__ = (
        Index("idx_dunning_tenant_event", "tenant_id", "event_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    subscription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant_subscriptions.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # NOTICE_J30, NOTICE_J7, NOTICE_J1, DUE_J0, PAST_DUE_J3, GRACE_J7, SUSPENDED
    sent_to_email: Mapped[str] = mapped_column(String(255), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BillingSettingsModel(Base):
    """Paramètres globaux de facturation configurés par le super-admin."""
    __tablename__ = "billing_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tax_rate_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tax_id_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    company_name: Mapped[str] = mapped_column(String(255), default="Pineapple OS SARL", nullable=False)
    company_address: Mapped[str] = mapped_column(Text, default="Douala, Cameroun", nullable=False)
    legal_notice: Mapped[Text] = mapped_column(Text, default="Facture payable en XAF FCFA. Sous réserve de validation comptable.", nullable=False)
    default_grace_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    default_trial_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# Legacy models preserved for backward compatibility
class SponsorshipModel(Base):
    __tablename__ = "sponsorships"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    target_tenant_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    budget_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[SponsorshipStatus] = mapped_column(
        Enum(SponsorshipStatus, name="sponsorship_status_enum"),
        nullable=False,
        default=SponsorshipStatus.PENDING,
    )
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CampusLicenseModel(Base):
    __tablename__ = "campus_licenses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False, unique=True)
    tier: Mapped[CampusLicenseTier] = mapped_column(
        Enum(CampusLicenseTier, name="campus_license_tier_enum"), nullable=False
    )
    max_certified_students: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AdCampaignModel(Base):
    """Campagne publicitaire pour le fil d'actualités des visiteurs."""
    __tablename__ = "ad_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    advertiser_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    target_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdCreativeModel(Base):
    """Visuel / contenu d'une publicité."""
    __tablename__ = "ad_creatives"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    headline: Mapped[str] = mapped_column(String(200), nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cta_text: Mapped[str] = mapped_column(String(100), default="En savoir plus", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdEventModel(Base):
    """Événements publicitaires (impressions / clics)."""
    __tablename__ = "ad_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    creative_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_creatives.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # IMPRESSION, CLICK
    ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)