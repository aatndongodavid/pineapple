# backend/src/trust_safety_context/application/dtos.py

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from trust_safety_context.domain.value_objects import (
    ModerationAction,
    ReportReason,
    ReportStatus,
)


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SubmitReportDTO(BaseDTO):
    target_type: str
    target_id: UUID
    reason: ReportReason


class ReportResponseDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    reporter_user_id: UUID
    target_type: str
    target_id: UUID
    reason: ReportReason
    status: ReportStatus
    created_at: datetime


class ReviewReportDTO(BaseDTO):
    report_id: UUID
    action: Optional[ModerationAction] = None
    resolution: ReportStatus  # RESOLVED ou DISMISSED attendu


class ReviewReportResponseDTO(BaseDTO):
    report_id: UUID
    status: ReportStatus
    moderation_action: Optional[ModerationAction]
    message: str