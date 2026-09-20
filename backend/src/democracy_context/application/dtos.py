import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ElectionCreateDTO(BaseModel):
    title: str
    election_type: str
    eligibility_rules: dict[str, Any] = Field(default_factory=dict)
    voting_start_at: datetime
    voting_end_at: datetime


class ElectionResponseDTO(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    election_type: str
    status: str
    eligibility_rules: dict[str, Any]
    voting_start_at: datetime
    voting_end_at: datetime
    total_voters_count: int = 0


class CastVoteDTO(BaseModel):
    election_id: uuid.UUID | None = None
    ballot: dict[str, Any] = Field(default_factory=dict)


class ElectionResultsDTO(BaseModel):
    election_id: uuid.UUID
    tenant_id: uuid.UUID
    results: dict[str, Any] = Field(default_factory=dict)
