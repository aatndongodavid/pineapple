"""0004 notifications multicanal tables

Revision ID: 0004_notifications_multicanal
Revises: 0003_timetable_and_rooms
Create Date: 2026-10-08 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_notifications_multicanal'
down_revision: Union[str, None] = '0003_timetable_and_rooms'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. outbox_events
    op.create_table(
        'outbox_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'PROCESSED', 'FAILED', name='outbox_event_status_enum'), server_default='PENDING', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_outbox_events_event_type'), 'outbox_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_outbox_events_status'), 'outbox_events', ['status'], unique=False)
    op.create_index(op.f('ix_outbox_events_tenant_id'), 'outbox_events', ['tenant_id'], unique=False)

    # 2. notification_templates
    op.create_table(
        'notification_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('channel', sa.Enum('IN_APP', 'PUSH', 'EMAIL', 'SMS', 'WHATSAPP', name='notification_channel_enum'), nullable=False),
        sa.Column('language', sa.String(length=10), server_default='fr', nullable=False),
        sa.Column('subject_template', sa.String(length=255), nullable=True),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('code', 'channel', 'language', name='uq_template_code_channel_lang'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_templates_code'), 'notification_templates', ['code'], unique=False)
    op.create_index(op.f('ix_notification_templates_tenant_id'), 'notification_templates', ['tenant_id'], unique=False)

    # 3. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('category', sa.Enum('CRITICAL', 'IMPORTANT', 'INFO', name='notification_category_enum'), nullable=False),
        sa.Column('criticality', sa.Enum('CRITICAL', 'IMPORTANT', 'INFO', name='notification_criticality_enum'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('deep_link', sa.String(length=500), nullable=True),
        sa.Column('dedup_key', sa.String(length=255), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_notifications_dedup_key'), 'notifications', ['dedup_key'], unique=False)
    op.create_index(op.f('ix_notifications_tenant_id'), 'notifications', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    # 4. notification_deliveries
    op.create_table(
        'notification_deliveries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('notification_id', sa.UUID(), nullable=False),
        sa.Column('channel', sa.Enum('IN_APP', 'PUSH', 'EMAIL', 'SMS', 'WHATSAPP', name='notification_channel_enum'), nullable=False),
        sa.Column('status', sa.Enum('QUEUED', 'SENT', 'DELIVERED', 'FAILED', 'SKIPPED', 'DEAD_LETTER', name='delivery_status_enum'), server_default='QUEUED', nullable=False),
        sa.Column('skipped_reason', sa.String(length=255), nullable=True),
        sa.Column('provider_name', sa.String(length=100), nullable=True),
        sa.Column('provider_ref', sa.String(length=255), nullable=True),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_deliveries_notification_id'), 'notification_deliveries', ['notification_id'], unique=False)
    op.create_index(op.f('ix_notification_deliveries_status'), 'notification_deliveries', ['status'], unique=False)

    # 5. notification_preferences
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'category', 'channel', name='uq_user_category_channel_pref'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_preferences_tenant_id'), 'notification_preferences', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=False)

    # 6. quiet_hours
    op.create_table(
        'quiet_hours',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('start_hour', sa.Integer(), server_default='21', nullable=False),
        sa.Column('end_hour', sa.Integer(), server_default='6', nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quiet_hours_tenant_id'), 'quiet_hours', ['tenant_id'], unique=False)

    # 7. push_subscriptions
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('p256dh', sa.Text(), nullable=False),
        sa.Column('auth', sa.Text(), nullable=False),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('endpoint'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_push_subscriptions_tenant_id'), 'push_subscriptions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_push_subscriptions_user_id'), 'push_subscriptions', ['user_id'], unique=False)

    # 8. channel_quotas
    op.create_table(
        'channel_quotas',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('period', sa.String(length=20), server_default='MONTHLY', nullable=False),
        sa.Column('max_limit', sa.Integer(), server_default='500', nullable=False),
        sa.Column('current_usage', sa.Integer(), server_default='0', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', 'channel', 'period', name='uq_tenant_channel_period_quota'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_channel_quotas_tenant_id'), 'channel_quotas', ['tenant_id'], unique=False)

    # 9. broadcasts
    op.create_table(
        'broadcasts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('author_id', sa.UUID(), nullable=False),
        sa.Column('audience_type', sa.Enum('TENANT_ALL', 'CLASS_GROUP', name='broadcast_audience_type_enum'), nullable=False),
        sa.Column('class_group_id', sa.UUID(), nullable=True),
        sa.Column('category', sa.String(length=50), server_default='IMPORTANT', nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('deep_link', sa.String(length=500), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'PENDING', 'SENT', 'FAILED', name='broadcast_status_enum'), server_default='PENDING', nullable=False),
        sa.Column('target_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_broadcasts_tenant_id'), 'broadcasts', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_broadcasts_tenant_id'), table_name='broadcasts')
    op.drop_table('broadcasts')

    op.drop_index(op.f('ix_channel_quotas_tenant_id'), table_name='channel_quotas')
    op.drop_table('channel_quotas')

    op.drop_index(op.f('ix_push_subscriptions_user_id'), table_name='push_subscriptions')
    op.drop_index(op.f('ix_push_subscriptions_tenant_id'), table_name='push_subscriptions')
    op.drop_table('push_subscriptions')

    op.drop_index(op.f('ix_quiet_hours_tenant_id'), table_name='quiet_hours')
    op.drop_table('quiet_hours')

    op.drop_index(op.f('ix_notification_preferences_user_id'), table_name='notification_preferences')
    op.drop_index(op.f('ix_notification_preferences_tenant_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')

    op.drop_index(op.f('ix_notification_deliveries_status'), table_name='notification_deliveries')
    op.drop_index(op.f('ix_notification_deliveries_notification_id'), table_name='notification_deliveries')
    op.drop_table('notification_deliveries')

    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_tenant_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_dedup_key'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_table('notifications')

    op.drop_index(op.f('ix_notification_templates_tenant_id'), table_name='notification_templates')
    op.drop_index(op.f('ix_notification_templates_code'), table_name='notification_templates')
    op.drop_table('notification_templates')

    op.drop_index(op.f('ix_outbox_events_tenant_id'), table_name='outbox_events')
    op.drop_index(op.f('ix_outbox_events_status'), table_name='outbox_events')
    op.drop_index(op.f('ix_outbox_events_event_type'), table_name='outbox_events')
    op.drop_table('outbox_events')

    op.execute("DROP TYPE IF EXISTS broadcast_status_enum")
    op.execute("DROP TYPE IF EXISTS broadcast_audience_type_enum")
    op.execute("DROP TYPE IF EXISTS delivery_status_enum")
    op.execute("DROP TYPE IF EXISTS notification_criticality_enum")
    op.execute("DROP TYPE IF EXISTS notification_category_enum")
    op.execute("DROP TYPE IF EXISTS notification_channel_enum")
    op.execute("DROP TYPE IF EXISTS outbox_event_status_enum")
