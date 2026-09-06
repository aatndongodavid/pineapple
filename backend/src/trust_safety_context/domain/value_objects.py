# backend/src/trust_safety_context/domain/value_objects.py

from enum import Enum


class ReportReason(str, Enum):
    """Motifs de signalement."""
    SPAM = "SPAM"
    HARASSMENT = "HARASSMENT"
    HATE_SPEECH = "HATE_SPEECH"
    FRAUD = "FRAUD"
    ELECTION_VIOLATION = "ELECTION_VIOLATION"


class ReportStatus(str, Enum):
    """État d'un signalement."""
    PENDING = "PENDING"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class ModerationAction(str, Enum):
    """Actions de modération possibles."""
    WARNING = "WARNING"
    CONTENT_REMOVED = "CONTENT_REMOVED"
    ACCOUNT_SUSPENDED = "ACCOUNT_SUSPENDED"