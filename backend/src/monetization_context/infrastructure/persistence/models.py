# backend/src/monetization_context/infrastructure/persistence/models.py

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
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
    target_tenant_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
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