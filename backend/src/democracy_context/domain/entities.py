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
    VOTING_OPEN = "OPEN"
    VOTING_CLOSED = "CLOSED"
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
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_eligible(self, user_academic_status: str, is_certified: bool, user_level: str = None) -> bool:
        if self.eligibility_rules.get("certified") and not is_certified:
            return False
        if "level" in self.eligibility_rules and user_level and self.eligibility_rules["level"] != user_level:
            return False
        return True

    def can_vote(self, at_time: datetime = None) -> bool:
        status_str = getattr(self.status, "value", str(self.status))
        if status_str not in ("OPEN", "VOTING_OPEN"):
            return False
        now = at_time or datetime.utcnow()
        if self.voting_start_at and now < self.voting_start_at:
            return False
        if self.voting_end_at and now > self.voting_end_at:
            return False
        return True

    def close_voting(self) -> None:
        self.status = ElectionStatus.VOTING_CLOSED


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
