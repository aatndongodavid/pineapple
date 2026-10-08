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


class CalendarExceptionType(str, Enum):
    HOLIDAY = "HOLIDAY"
    VACATION = "VACATION"
    EXAM_PERIOD = "EXAM_PERIOD"


class TimetableExceptionType(str, Enum):
    CANCELLED = "CANCELLED"
    MOVED = "MOVED"
    ROOM_CHANGED = "ROOM_CHANGED"
    TEACHER_CHANGED = "TEACHER_CHANGED"


class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ChangeRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

