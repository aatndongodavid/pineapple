# backend/src/trust_safety_context/application/use_cases.py

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from trust_safety_context.application.dtos import (
    ReviewReportDTO,
    ReviewReportResponseDTO,
    SubmitReportDTO,
)
from trust_safety_context.domain.entities import AuditLogEntry, Report
from trust_safety_context.domain.ports import TrustSafetyRepositoryPort
from trust_safety_context.domain.value_objects import (
    ModerationAction,
    ReportStatus,
)


class ReportNotFoundError(Exception):
    pass


class InvalidReviewError(Exception):
    pass


class SubmitReportUseCase:
    """Soumission d'un signalement par un utilisateur."""

    def __init__(self, trust_safety_repo: TrustSafetyRepositoryPort):
        self._repo = trust_safety_repo

    async def execute(
        self,
        reporter_user_id: UUID,
        tenant_id: UUID,
        dto: SubmitReportDTO,
    ) -> Report:
        report = Report(
            id=uuid4(),
            tenant_id=tenant_id,
            reporter_user_id=reporter_user_id,
            target_type=dto.target_type,
            target_id=dto.target_id,
            reason=dto.reason,
            status=ReportStatus.PENDING,
            created_at=datetime.utcnow(),
        )
        return await self._repo.save_report(report)


class ReviewReportUseCase:
    """Revue d'un signalement par un modérateur."""

    def __init__(self, trust_safety_repo: TrustSafetyRepositoryPort):
        self._repo = trust_safety_repo

    async def execute(
        self,
        moderator_user_id: UUID,
        tenant_id: UUID,
        dto: ReviewReportDTO,
    ) -> ReviewReportResponseDTO:
        report = await self._repo.get_report_by_id(dto.report_id, tenant_id)
        if not report:
            raise ReportNotFoundError("Report not found")

        # Validation basique : le statut demandé doit être RESOLVED ou DISMISSED
        if dto.resolution not in (ReportStatus.RESOLVED, ReportStatus.DISMISSED):
            raise InvalidReviewError("Resolution must be RESOLVED or DISMISSED")

        # Mise à jour du statut du signalement
        report.status = dto.resolution
        await self._repo.save_report(report)

        # Enregistrement dans le journal d'audit
        audit_entry = AuditLogEntry(
            id=uuid4(),
            tenant_id=tenant_id,
            action="report.reviewed",
            metadata={
                "report_id": str(report.id),
                "moderator_user_id": str(moderator_user_id),
                "resolution": dto.resolution.value,
                "moderation_action": dto.action.value if dto.action else None,
            },
            hash="",  # sera calculé dans le repository ou ici (simplifié)
            created_at=datetime.utcnow(),
        )
        # On peut calculer un hash simple (ex: sha256 du contenu) – à implémenter dans le repository
        # Ici on l'omet pour simplifier, mais on devrait le faire dans l'infrastructure.
        await self._repo.append_audit_log(audit_entry)

        # Appliquer l'action de modération si fournie
        # (ici on ne fait rien d'autre que l'enregistrer ; dans une vraie implémentation,
        # on appellerait d'autres contextes pour supprimer le contenu ou suspendre le compte)

        return ReviewReportResponseDTO(
            report_id=report.id,
            status=report.status,
            moderation_action=dto.action,
            message="Report reviewed successfully",
        )