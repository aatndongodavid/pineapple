# backend/src/trust_safety_context/infrastructure/persistence/repositories.py

import hashlib
import json
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from trust_safety_context.domain.entities import AuditLogEntry, Report
from trust_safety_context.domain.ports import TrustSafetyRepositoryPort
from trust_safety_context.domain.value_objects import ReportStatus
from trust_safety_context.infrastructure.persistence.models import (
    AuditLogEntryModel,
    ReportModel,
)


class PostgresTrustSafetyRepository(TrustSafetyRepositoryPort):
    """Implémentation PostgreSQL du port TrustSafetyRepositoryPort."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    # ----- Report -----
    @staticmethod
    def _report_to_entity(model: ReportModel) -> Report:
        return Report(
            id=model.id,
            tenant_id=model.tenant_id,
            reporter_user_id=model.reporter_user_id,
            target_type=model.target_type,
            target_id=model.target_id,
            reason=model.reason,
            status=model.status,
            created_at=model.created_at,
        )

    @staticmethod
    def _report_to_model(report: Report) -> ReportModel:
        return ReportModel(
            id=report.id,
            tenant_id=report.tenant_id,
            reporter_user_id=report.reporter_user_id,
            target_type=report.target_type,
            target_id=report.target_id,
            reason=report.reason,
            status=report.status,
            created_at=report.created_at,
        )

    async def save_report(self, report: Report) -> Report:
        async with self._session_factory() as session:
            model = self._report_to_model(report)
            try:
                await session.merge(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return report

    async def get_report_by_id(self, report_id: UUID, tenant_id: UUID) -> Optional[Report]:
        async with self._session_factory() as session:
            stmt = select(ReportModel).where(
                ReportModel.id == report_id,
                ReportModel.tenant_id == tenant_id,
            )
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._report_to_entity(model) if model else None

    async def list_reports(
        self, tenant_id: UUID, status: Optional[ReportStatus] = None
    ) -> List[Report]:
        async with self._session_factory() as session:
            stmt = select(ReportModel).where(ReportModel.tenant_id == tenant_id)
            if status is not None:
                stmt = stmt.where(ReportModel.status == status)
            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._report_to_entity(m) for m in models]

    # ----- Audit Log -----
    @staticmethod
    def _audit_to_entity(model: AuditLogEntryModel) -> AuditLogEntry:
        return AuditLogEntry(
            id=model.id,
            tenant_id=model.tenant_id,
            action=model.action,
            metadata=model.metadata,
            hash=model.hash,
            created_at=model.created_at,
        )

    @staticmethod
    def _audit_to_model(entry: AuditLogEntry) -> AuditLogEntryModel:
        # Calculer un hash d'intégrité simple si non fourni
        if not entry.hash:
            payload = (
                f"{entry.action}|{json.dumps(entry.metadata, sort_keys=True)}|{entry.created_at.isoformat()}"
            )
            entry.hash = hashlib.sha256(payload.encode()).hexdigest()
        return AuditLogEntryModel(
            id=entry.id,
            tenant_id=entry.tenant_id,
            action=entry.action,
            metadata=entry.metadata,
            hash=entry.hash,
            created_at=entry.created_at,
        )

    async def append_audit_log(self, entry: AuditLogEntry) -> AuditLogEntry:
        async with self._session_factory() as session:
            model = self._audit_to_model(entry)
            try:
                session.add(model)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return entry