# backend/src/notification_context/domain/value_objects.py

from enum import Enum


class NotificationCategory(str, Enum):
    CRITICAL = "CRITICAL"
    IMPORTANT = "IMPORTANT"
    INFO = "INFO"


class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"
    PUSH = "PUSH"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"


class DeliveryStatus(str, Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    DEAD_LETTER = "DEAD_LETTER"


class OutboxEventStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class BroadcastStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class BroadcastAudienceType(str, Enum):
    TENANT_ALL = "TENANT_ALL"
    CLASS_GROUP = "CLASS_GROUP"
