from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ElectionCreateDTO(BaseDTO):
    title: str
    election_type: str
    eligibility_rules: Dict
    voting_start_at: datetime
    voting_end_at: datetime


class MovementCreateDTO(BaseDTO):
    election_id: UUID
    name: str
    slogan: str
    program_text: str
    candidate_user_ids: List[UUID]


class CastVoteDTO(BaseDTO):
    election_id: UUID
    choice_id: str  # peut être un UUID de candidat ou un identifiant de choix


class ElectionResponseDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    title: str
    election_type: str
    status: str
    eligibility_rules: Dict
    voting_start_at: datetime
    voting_end_at: datetime
    total_voters_count: int


class ElectionResultsDTO(BaseDTO):
    election_id: UUID
    total_ballots: int
    tally_results: Dict[str, int]
    published_at: datetime