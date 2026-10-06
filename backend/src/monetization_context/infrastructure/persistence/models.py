import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from monetization_context.domain.value_objects import (
    CampusLicenseTier,
    SponsorshipStatus,
)
from shared_kernel.infrastructure.database import Base


class SponsorshipModel(Base):
    __tablename__ = "sponsorships"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    target_tenant_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    budget_amount: Mapped[int] = mapped_column(Integer, nullable=False)
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