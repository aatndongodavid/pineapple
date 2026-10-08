import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

from identity_context.infrastructure.persistence.models import Base
from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import JSON


class AuditLogModel(Base):
    """Journal d'audit pour les actions sensibles."""
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=True)
    user_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


async def log_audit_event(
    db: AsyncSession,
    action: str,
    resource_type: str,
    tenant_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Enregistre un événement sensible dans le journal d'audit."""
    stmt = insert(AuditLogModel).values(
        id=str(uuid.uuid4()),
        tenant_id=str(tenant_id) if tenant_id else None,
        user_id=str(user_id) if user_id else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
    )
    await db.execute(stmt)
