# backend/src/monetization_context/infrastructure/persistence/models.py

import uuid
from datetime import datetime
from typing import List, Optional

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    lines: Mapped[List["InvoiceLineModel"]] = relationship(
        "InvoiceLineModel", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin"
    )


class InvoiceLineModel(Base):
    """Lignes de détail d'une facture."""
    __tablename__ = "invoice_lines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)

    invoice: Mapped["InvoiceModel"] = relationship("InvoiceModel", back_populates="lines")


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
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    amount_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # MOBILE_MONEY, MANUAL
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_ref: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    phone_number_masked: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class PaymentEventModel(Base):
    """Événements de Webhook récepteurs idempotents."""
    __tablename__ = "payment_events"
    __table_args__ = (
        UniqueConstraint("provider_name", "provider_event_id", name="uq_payment_event_provider_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), default="PAYMENT_NOTIFICATION", nullable=False)
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


class AdvertiserModel(Base):
    """Annonceur en libre-service (compte entreprise / publicitaire)."""
    __tablename__ = "advertisers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="CM", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # PENDING, ACTIVE, SUSPENDED

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AdvertiserUserModel(Base):
    """Lien entre un utilisateur et un compte annonceur."""
    __tablename__ = "advertiser_users"
    __table_args__ = (
        UniqueConstraint("advertiser_id", "user_id", name="uq_advertiser_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    advertiser_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("advertisers.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="ADVERTISER", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdWalletModel(Base):
    """Portefeuille prépayé en XAF d'un annonceur."""
    __tablename__ = "ad_wallets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    advertiser_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("advertisers.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    balance_xaf: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WalletTransactionModel(Base):
    """Journal immuable des transactions de portefeuille (Crédits, Débits de diffusion, Remboursements)."""
    __tablename__ = "wallet_transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_wallets.id", ondelete="CASCADE"), index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # DEPOSIT, AD_DELIVERY_DEBIT, REFUND, ADJUSTMENT
    amount_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)  # Positif pour dépôt/remboursement, négatif pour débit
    balance_after_xaf: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdCampaignModel(Base):
    """Campagne publicitaire ciblée sur les visiteurs."""
    __tablename__ = "ad_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    advertiser_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("advertisers.id", ondelete="CASCADE"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    advertiser_name: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(String(50), default="AWARENESS", nullable=False)  # AWARENESS, TRAFFIC
    billing_model: Mapped[str] = mapped_column(String(50), default="CPM", nullable=False)  # CPM, CPC, FLAT_PERIOD
    unit_price_xaf: Mapped[int] = mapped_column(BigInteger, default=1000, nullable=False)  # Prix par 1000 imp ou par clic
    total_budget_xaf: Mapped[int] = mapped_column(BigInteger, default=50000, nullable=False)
    spent_xaf: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    daily_budget_xaf: Mapped[int] = mapped_column(BigInteger, default=5000, nullable=False)
    daily_spent_xaf: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    frequency_cap_per_session: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    pacing_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE", nullable=False)  # DRAFT, PENDING_REVIEW, ACTIVE, PAUSED, ENDED, REJECTED
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    target_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdTargetingRuleModel(Base):
    """Critères de ciblage géographique/comportemental grossier pour une campagne."""
    __tablename__ = "ad_targeting_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_campaigns.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    cities_regions_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    languages_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    device_types_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    hours_of_day_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)


class AdCreativeModel(Base):
    """Visuel / contenu d'une publicité avec modération."""
    __tablename__ = "ad_creatives"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    headline: Mapped[str] = mapped_column(String(200), nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cta_text: Mapped[str] = mapped_column(String(100), default="En savoir plus", nullable=False)
    target_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    review_status: Mapped[str] = mapped_column(String(50), default="APPROVED", nullable=False)  # PENDING_REVIEW, APPROVED, REJECTED
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdReviewEventModel(Base):
    """Historique des événements de modération des créations publicitaires."""
    __tablename__ = "ad_review_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    creative_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_creatives.id", ondelete="CASCADE"), index=True, nullable=False)
    reviewer_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    previous_status: Mapped[str] = mapped_column(String(50), nullable=False)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdImpressionRawModel(Base):
    """Impressions brutes en direct (pour comptage et vérification de jeton)."""
    __tablename__ = "ad_impressions_raw"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    creative_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_creatives.id", ondelete="CASCADE"), index=True, nullable=False)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    visitor_session_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdStatsDailyModel(Base):
    """Agrégation quotidienne des statistiques de diffusion et de dépense."""
    __tablename__ = "ad_stats_daily"
    __table_args__ = (
        UniqueConstraint("campaign_id", "creative_id", "stat_date", name="uq_ad_stats_daily_cmp_crt_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_campaigns.id", ondelete="CASCADE"), index=True, nullable=False)
    creative_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_creatives.id", ondelete="CASCADE"), index=True, nullable=False)
    stat_date: Mapped[str] = mapped_column(String(10), index=True, nullable=False)  # YYYY-MM-DD
    impressions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    spent_xaf: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)


class AdUserFeedbackModel(Base):
    """Signalements et masquages d'annonces par les visiteurs."""
    __tablename__ = "ad_user_feedback"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    creative_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ad_creatives.id", ondelete="CASCADE"), index=True, nullable=False)
    visitor_session_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)  # HIDE, REPORT
    reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AdPolicyRuleModel(Base):
    """Règles de politique et mots-clés interdits configurés par la plateforme."""
    __tablename__ = "ad_policy_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    forbidden_keywords_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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