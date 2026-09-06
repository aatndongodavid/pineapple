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