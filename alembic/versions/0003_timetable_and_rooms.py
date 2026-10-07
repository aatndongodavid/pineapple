"""0003 timetable and rooms tables

Revision ID: 0003_timetable_and_rooms
Revises: 0002_billing_and_payments
Create Date: 2026-10-07 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_timetable_and_rooms'
down_revision: Union[str, None] = '0002_billing_and_payments'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. academic_terms
    op.create_table(
        'academic_terms',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('academic_year', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_academic_terms_tenant_id'), 'academic_terms', ['tenant_id'], unique=False)

    # 2. calendar_exceptions
    op.create_table(
        'calendar_exceptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('term_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('exception_type', sa.Enum('HOLIDAY', 'VACATION', 'EXAM_PERIOD', name='calendar_exception_type_enum'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['term_id'], ['academic_terms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_exceptions_tenant_id'), 'calendar_exceptions', ['tenant_id'], unique=False)

    # 3. subjects
    op.create_table(
        'subjects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('credits', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subjects_tenant_id'), 'subjects', ['tenant_id'], unique=False)

    # 4. course_offerings
    op.create_table(
        'course_offerings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('term_id', sa.UUID(), nullable=False),
        sa.Column('subject_id', sa.UUID(), nullable=False),
        sa.Column('class_group_id', sa.UUID(), nullable=False),
        sa.Column('teacher_id', sa.UUID(), nullable=True),
        sa.Column('color_code', sa.String(length=20), server_default='#3182CE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['term_id'], ['academic_terms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_course_offerings_class_group_id'), 'course_offerings', ['class_group_id'], unique=False)
    op.create_index(op.f('ix_course_offerings_subject_id'), 'course_offerings', ['subject_id'], unique=False)
    op.create_index(op.f('ix_course_offerings_tenant_id'), 'course_offerings', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_course_offerings_term_id'), 'course_offerings', ['term_id'], unique=False)

    # 5. timetable_rules
    op.create_table(
        'timetable_rules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('course_offering_id', sa.UUID(), nullable=False),
        sa.Column('room_id', sa.UUID(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('recurrence_rule', sa.String(length=200), server_default='FREQ=WEEKLY', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['course_offering_id'], ['course_offerings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', 'room_id', 'day_of_week', 'start_time', name='uq_timetable_room_slot'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_timetable_rules_course_offering_id'), 'timetable_rules', ['course_offering_id'], unique=False)
    op.create_index(op.f('ix_timetable_rules_room_id'), 'timetable_rules', ['room_id'], unique=False)
    op.create_index(op.f('ix_timetable_rules_tenant_id'), 'timetable_rules', ['tenant_id'], unique=False)
    op.create_index('ix_timetable_rules_lookup', 'timetable_rules', ['tenant_id', 'room_id', 'day_of_week'], unique=False)

    # 6. timetable_exceptions
    op.create_table(
        'timetable_exceptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('rule_id', sa.UUID(), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('exception_type', sa.Enum('CANCELLED', 'MOVED', 'ROOM_CHANGED', 'TEACHER_CHANGED', name='timetable_exception_type_enum'), nullable=False),
        sa.Column('new_room_id', sa.UUID(), nullable=True),
        sa.Column('new_teacher_id', sa.UUID(), nullable=True),
        sa.Column('new_start_time', sa.Time(), nullable=True),
        sa.Column('new_end_time', sa.Time(), nullable=True),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('author_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['new_room_id'], ['rooms.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['new_teacher_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rule_id'], ['timetable_rules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_timetable_exceptions_rule_id'), 'timetable_exceptions', ['rule_id'], unique=False)
    op.create_index(op.f('ix_timetable_exceptions_tenant_id'), 'timetable_exceptions', ['tenant_id'], unique=False)

    # 7. room_features
    op.create_table(
        'room_features',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('room_id', sa.UUID(), nullable=False),
        sa.Column('feature_name', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_room_features_room_id'), 'room_features', ['room_id'], unique=False)
    op.create_index(op.f('ix_room_features_tenant_id'), 'room_features', ['tenant_id'], unique=False)

    # 8. room_reservations
    op.create_table(
        'room_reservations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('room_id', sa.UUID(), nullable=False),
        sa.Column('requester_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('reservation_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='room_reservation_status_enum'), server_default='PENDING', nullable=False),
        sa.Column('approved_by_id', sa.UUID(), nullable=True),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_room_reservations_room_id'), 'room_reservations', ['room_id'], unique=False)
    op.create_index(op.f('ix_room_reservations_tenant_id'), 'room_reservations', ['tenant_id'], unique=False)

    # 9. timetable_change_requests
    op.create_table(
        'timetable_change_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('teacher_id', sa.UUID(), nullable=False),
        sa.Column('rule_id', sa.UUID(), nullable=True),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('requested_type', sa.String(length=50), nullable=False),
        sa.Column('proposed_room_id', sa.UUID(), nullable=True),
        sa.Column('proposed_start_time', sa.Time(), nullable=True),
        sa.Column('proposed_end_time', sa.Time(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='change_request_status_enum'), server_default='PENDING', nullable=False),
        sa.Column('reviewed_by_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['proposed_room_id'], ['rooms.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rule_id'], ['timetable_rules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_timetable_change_requests_tenant_id'), 'timetable_change_requests', ['tenant_id'], unique=False)

    # 10. ics_tokens
    op.create_table(
        'ics_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('class_group_id', sa.UUID(), nullable=True),
        sa.Column('token', sa.String(length=100), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ics_tokens_token'), 'ics_tokens', ['token'], unique=True)
    op.create_index(op.f('ix_ics_tokens_tenant_id'), 'ics_tokens', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ics_tokens_tenant_id'), table_name='ics_tokens')
    op.drop_index(op.f('ix_ics_tokens_token'), table_name='ics_tokens')
    op.drop_table('ics_tokens')

    op.drop_index(op.f('ix_timetable_change_requests_tenant_id'), table_name='timetable_change_requests')
    op.drop_table('timetable_change_requests')

    op.drop_index(op.f('ix_room_reservations_tenant_id'), table_name='room_reservations')
    op.drop_index(op.f('ix_room_reservations_room_id'), table_name='room_reservations')
    op.drop_table('room_reservations')

    op.drop_index(op.f('ix_room_features_tenant_id'), table_name='room_features')
    op.drop_index(op.f('ix_room_features_room_id'), table_name='room_features')
    op.drop_table('room_features')

    op.drop_index(op.f('ix_timetable_exceptions_tenant_id'), table_name='timetable_exceptions')
    op.drop_index(op.f('ix_timetable_exceptions_rule_id'), table_name='timetable_exceptions')
    op.drop_table('timetable_exceptions')

    op.drop_index('ix_timetable_rules_lookup', table_name='timetable_rules')
    op.drop_index(op.f('ix_timetable_rules_tenant_id'), table_name='timetable_rules')
    op.drop_index(op.f('ix_timetable_rules_room_id'), table_name='timetable_rules')
    op.drop_index(op.f('ix_timetable_rules_course_offering_id'), table_name='timetable_rules')
    op.drop_table('timetable_rules')

    op.drop_index(op.f('ix_course_offerings_term_id'), table_name='course_offerings')
    op.drop_index(op.f('ix_course_offerings_tenant_id'), table_name='course_offerings')
    op.drop_index(op.f('ix_course_offerings_subject_id'), table_name='course_offerings')
    op.drop_index(op.f('ix_course_offerings_class_group_id'), table_name='course_offerings')
    op.drop_table('course_offerings')

    op.drop_index(op.f('ix_subjects_tenant_id'), table_name='subjects')
    op.drop_table('subjects')

    op.drop_index(op.f('ix_calendar_exceptions_tenant_id'), table_name='calendar_exceptions')
    op.drop_table('calendar_exceptions')

    op.drop_index(op.f('ix_academic_terms_tenant_id'), table_name='academic_terms')
    op.drop_table('academic_terms')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS calendar_exception_type_enum")
    op.execute("DROP TYPE IF EXISTS timetable_exception_type_enum")
    op.execute("DROP TYPE IF EXISTS room_reservation_status_enum")
    op.execute("DROP TYPE IF EXISTS change_request_status_enum")
