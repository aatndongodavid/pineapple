# backend/src/trust_safety_context/domain/entities.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from trust_safety_context.domain.value_objects import ReportReason, ReportStatus


@dataclass
class Report:
    """Signalement d'un contenu ou d'un comportement."""
    id: UUID
    tenant_id: UUID
    reporter_user_id: UUID
    target_type: str          # ex: "post", "user", "comment", "election"
    target_id: UUID
    reason: ReportReason
    status: ReportStatus = ReportStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditLogEntry:
    """
    Entrée du journal d'audit immuable.
    Chaque action de modération ou sécurité y est consignée avec un hash d'intégrité.
    """
    id: UUID
    tenant_id: UUID
    action: str               # ex: "report.created", "moderation.action.applied"
    metadata: Dict[str, Any]  # informations contextuelles
    hash: str                 # empreinte d'intégrité (sha256 par exemple)
    created_at: datetime = field(default_factory=datetime.utcnow)