# backend/src/opportunities_context/domain/entities.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from opportunities_context.domain.value_objects import (
    ApplicationStatus,
    OpportunityStatus,
    OpportunityType,
)


@dataclass
class ProjectApplication:
    """Candidature d'un étudiant à une opportunité."""
    id: UUID
    opportunity_id: UUID
    applicant_user_id: UUID
    cover_letter: str
    status: ApplicationStatus
    applied_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Opportunity:
    """
    Agrégat racine représentant une opportunité publiée sur la plateforme.
    """
    id: UUID
    tenant_id: UUID
    creator_id: UUID
    title: str
    description: str
    type: OpportunityType
    required_skills: List[str] = field(default_factory=list)
    status: OpportunityStatus = OpportunityStatus.DRAFT
    max_applicants: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)