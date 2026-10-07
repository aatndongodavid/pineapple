# backend/src/shared_kernel/domain/events.py

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class DomainEvent:
    """Base class for all domain events in Pineapple OS."""
    event_type: str
    tenant_id: uuid.UUID
    payload: Dict[str, Any]
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "tenant_id": str(self.tenant_id),
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ClassAnnouncementPublishedEvent(DomainEvent):
    def __init__(self, tenant_id: uuid.UUID, class_group_id: uuid.UUID, announcement_id: uuid.UUID, title: str, author_id: uuid.UUID):
        super().__init__(
            event_type="CLASS_ANNOUNCEMENT_PUBLISHED",
            tenant_id=tenant_id,
            payload={
                "class_group_id": str(class_group_id),
                "announcement_id": str(announcement_id),
                "title": title,
                "author_id": str(author_id),
            }
        )


@dataclass
class CourseCancelledEvent(DomainEvent):
    def __init__(self, tenant_id: uuid.UUID, rule_id: uuid.UUID, target_date: str, reason: str):
        super().__init__(
            event_type="COURSE_CANCELLED",
            tenant_id=tenant_id,
            payload={
                "rule_id": str(rule_id),
                "target_date": target_date,
                "reason": reason,
            }
        )


@dataclass
class RoomChangedEvent(DomainEvent):
    def __init__(self, tenant_id: uuid.UUID, rule_id: uuid.UUID, target_date: str, new_room_name: str):
        super().__init__(
            event_type="ROOM_CHANGED",
            tenant_id=tenant_id,
            payload={
                "rule_id": str(rule_id),
                "target_date": target_date,
                "new_room_name": new_room_name,
            }
        )


@dataclass
class MembershipClaimReviewedEvent(DomainEvent):
    def __init__(self, tenant_id: uuid.UUID, user_id: uuid.UUID, status: str, role: str):
        super().__init__(
            event_type="MEMBERSHIP_CLAIM_REVIEWED",
            tenant_id=tenant_id,
            payload={
                "user_id": str(user_id),
                "status": status,
                "role": role,
            }
        )


@dataclass
class InvoiceDueEvent(DomainEvent):
    def __init__(self, tenant_id: uuid.UUID, user_id: uuid.UUID, invoice_id: uuid.UUID, amount_xaf: int, due_date: str):
        super().__init__(
            event_type="INVOICE_DUE",
            tenant_id=tenant_id,
            payload={
                "user_id": str(user_id),
                "invoice_id": str(invoice_id),
                "amount_xaf": amount_xaf,
                "due_date": due_date,
            }
        )


@dataclass
class SecurityAlertEvent(DomainEvent):
    def __init__(self, tenant_id: uuid.UUID, user_id: uuid.UUID, alert_type: str, ip_address: str):
        super().__init__(
            event_type="SECURITY_ALERT",
            tenant_id=tenant_id,
            payload={
                "user_id": str(user_id),
                "alert_type": alert_type,
                "ip_address": ip_address,
            }
        )


@dataclass
class ElectionOpenedEvent(DomainEvent):
    def __init__(self, tenant_id: uuid.UUID, election_id: uuid.UUID, title: str):
        super().__init__(
            event_type="ELECTION_OPENED",
            tenant_id=tenant_id,
            payload={
                "election_id": str(election_id),
                "title": title,
            }
        )
