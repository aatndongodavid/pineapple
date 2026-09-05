# backend/src/monetization_context/domain/entities.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from monetization_context.domain.value_objects import (
    CampusLicenseTier,
    SponsorshipStatus,
)
from shared_kernel.domain.value_objects import Money


@dataclass
class Sponsorship:
    """Contrat de sponsoring d'une organisation vers des audiences ciblées."""
    id: UUID
    tenant_id: UUID
    organization_id: UUID
    target_tenant_ids: List[UUID]
    budget: Money
    status: SponsorshipStatus
    start_date: datetime
    end_date: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CampusLicense:
    """Licence souscrite par un établissement pour utiliser Pineapple."""
    id: UUID
    tenant_id: UUID
    tier: CampusLicenseTier
    max_certified_students: int
    is_active: bool
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)