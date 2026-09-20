from dataclasses import dataclass
from enum import Enum


class DocumentType(str, Enum):
    COURSE = "COURSE"
    CORRECTION = "CORRECTION"
    EXAM = "EXAM"
    OTHER = "OTHER"


class AccessStatus(str, Enum):
    FREE = "FREE"
    PREMIUM_LOCKED = "PREMIUM_LOCKED"
    PURCHASED = "PURCHASED"


@dataclass(frozen=True)
class WatermarkMetadata:
    user_matricule: str
    ip_address: str
    timestamp: str
