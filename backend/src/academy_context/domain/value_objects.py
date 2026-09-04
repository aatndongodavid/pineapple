from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from shared_kernel.domain.value_objects import DomainValidationError


class DocumentType(str, Enum):
    """Type de document académique."""
    COURSE = "COURSE"
    TD = "TD"
    TP = "TP"
    EXAM = "EXAM"
    CORRIGE_PREMIUM = "CORRIGE_PREMIUM"
    RESEARCH_PAPER = "RESEARCH_PAPER"


class AccessStatus(str, Enum):
    """Statut d'accès à un document académique."""
    FREE = "FREE"
    PREMIUM_LOCKED = "PREMIUM_LOCKED"
    PURCHASED = "PURCHASED"
    UNLIMITED = "UNLIMITED"


@dataclass(frozen=True)
class WatermarkMetadata:
    """
    Métadonnées injectées dynamiquement dans le Pineapple Reader
    pour prévenir les fuites et tracer les accès.
    """
    matricule: str
    user_id: UUID
    timestamp: datetime
    ip_address: str

    def __post_init__(self) -> None:
        if not self.matricule or not self.matricule.strip():
            raise DomainValidationError("WatermarkMetadata.matricule cannot be empty.")
        if not isinstance(self.user_id, UUID):
            raise DomainValidationError("WatermarkMetadata.user_id must be a UUID.")
        if not isinstance(self.timestamp, datetime):
            raise DomainValidationError("WatermarkMetadata.timestamp must be a datetime.")
        if not self.ip_address or not self.ip_address.strip():
            raise DomainValidationError("WatermarkMetadata.ip_address cannot be empty.")