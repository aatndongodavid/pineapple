import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

class ElectionStatus(str, Enum):
    DRAFT = "DRAFT"
    CAMPAIGN = "CAMPAIGN"
    UPCOMING = "UPCOMING"
    OPEN = "OPEN"
    VOTING_OPEN = "VOTING_OPEN"
    VOTING_CLOSED = "VOTING_CLOSED"
    RESULTS_PUBLISHED = "RESULTS_PUBLISHED"
    ARCHIVED = "ARCHIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class MovementStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


@dataclass
class Election:
    id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    election_type: str
    status: ElectionStatus
    eligibility_rules: dict[str, Any]
    voting_start_at: datetime
    voting_end_at: datetime


@dataclass
class Vote:
    id: uuid.UUID
    election_id: uuid.UUID
    tenant_id: uuid.UUID
    voter_hash: str
    encrypted_vote: str
    cast_at: datetime


@dataclass
class AuditLedgerEntry:
    id: uuid.UUID
    tenant_id: uuid.UUID
    action: str
    metadata: dict[str, Any] = field(default_factory=dict)
    hash: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
