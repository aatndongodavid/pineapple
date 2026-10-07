# backend/src/notification_context/infrastructure/persistence/models.py

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from notification_context.domain.value_objects import (
    BroadcastAudienceType,
    BroadcastStatus,
    DeliveryStatus,
    NotificationCategory,
    NotificationChannel,
    OutboxEventStatus,
)
from shared_kernel.infrastructure.database import Base


class OutboxEventModel(Base):
    """Événements métier capturés de façon transactionnelle pour traitement asynchrone."""
    __tablename__ = "outbox_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[OutboxEventStatus] = mapped_column(
        Enum(OutboxEventStatus, name="outbox_event_status_enum"), default=OutboxEventStatus.PENDING, index=True, nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationTemplateModel(Base):
    """Gabarits de notifications localisés (fr/en) par canal et catégorie."""
    __tablename__ = "notification_templates"
    __table_args__ = (
        UniqueConstraint("code", "channel", "language", name="uq_template_code_channel_lang"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=True)
    code: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel, name="notification_channel_enum"), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="fr", nullable=False)
    subject_template: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NotificationModel(Base):
    """Notification générée et distribuée à un destinataire."""
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    category: Mapped[NotificationCategory] = mapped_column(Enum(NotificationCategory, name="notification_category_enum"), nullable=False)
    criticality: Mapped[NotificationCategory] = mapped_column(Enum(NotificationCategory, name="notification_criticality_enum"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    deep_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    dedup_key: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)


class NotificationDeliveryModel(Base):
    """Suivi de la livraison d'une notification sur un canal donné."""
    __tablename__ = "notification_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    notification_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("notifications.id", ondelete="CASCADE"), index=True, nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel, name="notification_channel_enum"), nullable=False)
    status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus, name="delivery_status_enum"), default=DeliveryStatus.QUEUED, index=True, nullable=False)
    skipped_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    provider_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class NotificationPreferenceModel(Base):
    """Préférences utilisateur par catégorie et par canal."""
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "category", "channel", name="uq_user_category_channel_pref"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class QuietHoursModel(Base):
    """Plages d'heures calmes définies par un utilisateur."""
    __tablename__ = "quiet_hours"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    start_hour: Mapped[int] = mapped_column(Integer, default=21, nullable=False)
    end_hour: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PushSubscriptionModel(Base):
    """Abonnements Web Push VAPID associés au navigateur d'un utilisateur."""
    __tablename__ = "push_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    endpoint: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    auth: Mapped[str] = mapped_column(Text, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ChannelQuotaModel(Base):
    """Consommation et plafonds de quotas payants par canal (ex: SMS) et par tenant."""
    __tablename__ = "channel_quotas"
    __table_args__ = (
        UniqueConstraint("tenant_id", "channel", "period", name="uq_tenant_channel_period_quota"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(20), default="MONTHLY", nullable=False)
    max_limit: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    current_usage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BroadcastModel(Base):
    """Campagne d'envoi ciblé (diffusion) initiée par un administrateur ou un délégué."""
    __tablename__ = "broadcasts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    audience_type: Mapped[BroadcastAudienceType] = mapped_column(Enum(BroadcastAudienceType, name="broadcast_audience_type_enum"), nullable=False)
    class_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("class_groups.id", ondelete="SET NULL"), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="IMPORTANT", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    deep_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[BroadcastStatus] = mapped_column(Enum(BroadcastStatus, name="broadcast_status_enum"), default=BroadcastStatus.PENDING, nullable=False)
    target_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
