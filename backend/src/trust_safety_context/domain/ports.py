# backend/src/trust_safety_context/domain/ports.py

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from trust_safety_context.domain.entities import AuditLogEntry, Report
from trust_safety_context.domain.value_objects import ReportStatus


class TrustSafetyRepositoryPort(ABC):
    """Port de persistance pour le contexte Trust & Safety."""

    @abstractmethod
    async def save_report(self, report: Report) -> Report:
        """Sauvegarde un signalement."""
        raise NotImplementedError

    @abstractmethod
    async def get_report_by_id(
        self, report_id: UUID, tenant_id: UUID
    ) -> Optional[Report]:
        """Récupère un signalement par son identifiant et tenant."""
        raise NotImplementedError

    @abstractmethod
    async def list_reports(
        self,
        tenant_id: UUID,
        status: Optional[ReportStatus] = None,
    ) -> List[Report]:
        """Liste les signalements d'un tenant avec filtre optionnel de statut."""
        raise NotImplementedError

    @abstractmethod
    async def append_audit_log(self, entry: AuditLogEntry) -> AuditLogEntry:
        """Ajoute une entrée au journal d'audit immuable."""
        raise NotImplementedError