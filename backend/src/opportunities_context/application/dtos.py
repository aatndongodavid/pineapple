# backend/src/opportunities_context/application/dtos.py

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from opportunities_context.domain.value_objects import (
    ApplicationStatus,
    OpportunityStatus,
    OpportunityType,
)


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OpportunityCreateDTO(BaseDTO):
    title: str
    description: str
    type: OpportunityType
    required_skills: List[str] = []
    max_applicants: Optional[int] = None
    status: OpportunityStatus = OpportunityStatus.DRAFT


class OpportunityResponseDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    creator_id: UUID
    title: str
    description: str
    type: OpportunityType
    required_skills: List[str]
    status: OpportunityStatus
    max_applicants: Optional[int]
    created_at: datetime


class ApplicationCreateDTO(BaseDTO):
    opportunity_id: UUID
    cover_letter: str


class ApplicationResponseDTO(BaseDTO):
    id: UUID
    opportunity_id: UUID
    applicant_user_id: UUID
    cover_letter: str
    status: ApplicationStatus
    applied_at: datetime