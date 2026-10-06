"""0001_baseline

Revision ID: 0001_baseline
Revises: 
Create Date: 2026-10-05 23:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('phone_number', sa.String(length=50), nullable=True),
        sa.Column('user_type', sa.String(length=50), nullable=False, server_default='STANDARD'),
        sa.Column('account_status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('verification_status', sa.String(length=50), nullable=False, server_default='UNVERIFIED'),
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Tenants
    op.create_table(
        'tenants',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('enrollment_mode', sa.String(length=50), nullable=False, server_default='BOTH'),
        sa.Column('auto_approve_claims', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('current_academic_year', sa.String(length=20), nullable=False, server_default='2026-2027'),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='Africa/Douala'),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False, server_default='Cameroun'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenants_code'), 'tenants', ['code'], unique=True)

    # 3. Tenant Subscriptions
    op.create_table(
        'tenant_subscriptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=False, server_default='STANDARD'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('seats_limit', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('starts_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('grace_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('payment_ref', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenant_subscriptions_tenant_id'), 'tenant_subscriptions', ['tenant_id'])

    # 4. Class Groups
    op.create_table(
        'class_groups',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('faculty', sa.String(length=100), nullable=True),
        sa.Column('filiere', sa.String(length=100), nullable=True),
        sa.Column('level', sa.String(length=50), nullable=True),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'code', 'academic_year', name='uq_class_group_code_year')
    )
    op.create_index(op.f('ix_class_groups_tenant_id'), 'class_groups', ['tenant_id'])

    # 5. Import Batches
    op.create_table(
        'import_batches',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors_json', sa.Text(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Roster Entries
    op.create_table(
        'roster_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('matricule', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('birth_date', sa.String(length=255), nullable=False),
        sa.Column('birth_place', sa.String(length=255), nullable=False),
        sa.Column('norm_matricule', sa.String(length=100), nullable=False),
        sa.Column('norm_first_name', sa.String(length=100), nullable=False),
        sa.Column('norm_last_name', sa.String(length=100), nullable=False),
        sa.Column('norm_birth_date', sa.String(length=50), nullable=False),
        sa.Column('norm_birth_place', sa.String(length=100), nullable=False),
        sa.Column('class_group_id', sa.UUID(), nullable=True),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('official_email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='NOT_CLAIMED'),
        sa.Column('claimed_by_user_id', sa.UUID(), nullable=True),
        sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('import_batch_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['claimed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['import_batch_id'], ['import_batches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'matricule', 'academic_year', name='uq_roster_matricule_year')
    )
    op.create_index(op.f('ix_roster_entries_matricule'), 'roster_entries', ['matricule'])
    op.create_index(op.f('ix_roster_entries_norm_matricule'), 'roster_entries', ['norm_matricule'])
    op.create_index(op.f('ix_roster_entries_tenant_id'), 'roster_entries', ['tenant_id'])

    # 7. Memberships
    op.create_table(
        'memberships',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('roster_entry_id', sa.UUID(), nullable=True),
        sa.Column('class_group_id', sa.UUID(), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='STUDENT'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('joined_via', sa.String(length=50), nullable=False, server_default='CLAIM'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['roster_entry_id'], ['roster_entries.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('roster_entry_id')
    )
    op.create_index(op.f('ix_memberships_tenant_id'), 'memberships', ['tenant_id'])
    op.create_index(op.f('ix_memberships_user_id'), 'memberships', ['user_id'])

    # 8. Invitations
    op.create_table(
        'invitations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('roster_entry_id', sa.UUID(), nullable=False),
        sa.Column('identifier', sa.String(length=100), nullable=False),
        sa.Column('secret_hash', sa.String(length=255), nullable=False),
        sa.Column('email_sent_to', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('last_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['roster_entry_id'], ['roster_entries.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invitations_identifier'), 'invitations', ['identifier'], unique=True)
    op.create_index(op.f('ix_invitations_tenant_id'), 'invitations', ['tenant_id'])

    # 9. Enrollment Attempts
    op.create_table(
        'enrollment_attempts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('ip', sa.String(length=50), nullable=False),
        sa.Column('kind', sa.String(length=50), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_enrollment_attempts_ip'), 'enrollment_attempts', ['ip'])

    # 10. Class Delegates
    op.create_table(
        'class_delegates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('class_group_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('kind', sa.String(length=50), nullable=False, server_default='TITULAIRE'),
        sa.Column('appointed_by', sa.UUID(), nullable=False),
        sa.Column('appointed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['appointed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['revoked_by'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_delegates_class_group_id'), 'class_delegates', ['class_group_id'])
    op.create_index(op.f('ix_class_delegates_tenant_id'), 'class_delegates', ['tenant_id'])
    op.create_index(op.f('ix_class_delegates_user_id'), 'class_delegates', ['user_id'])

    # 11. Certification Documents
    op.create_table(
        'certification_documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('file_key', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 12. Rooms
    op.create_table(
        'rooms',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('building', sa.String(length=100), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='FREE'),
        sa.Column('declared_by_user_id', sa.UUID(), nullable=True),
        sa.Column('class_group_id', sa.UUID(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['declared_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rooms_tenant_id'), 'rooms', ['tenant_id'])

    # 13. Room Status Declarations
    op.create_table(
        'room_status_declarations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('room_id', sa.UUID(), nullable=False),
        sa.Column('class_group_id', sa.UUID(), nullable=True),
        sa.Column('declared_by_user_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('declared_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['declared_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_room_status_declarations_room_id'), 'room_status_declarations', ['room_id'])
    op.create_index(op.f('ix_room_status_declarations_tenant_id'), 'room_status_declarations', ['tenant_id'])

    # 14. Class Announcements
    op.create_table(
        'class_announcements',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('class_group_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('author_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id']),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_class_announcements_class_group_id'), 'class_announcements', ['class_group_id'])
    op.create_index(op.f('ix_class_announcements_tenant_id'), 'class_announcements', ['tenant_id'])

    # 15. Class Incidents
    op.create_table(
        'class_incidents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('class_group_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='TEACHER_ABSENT'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'),
        sa.Column('reported_by', sa.UUID(), nullable=False),
        sa.Column('resolved_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reported_by'], ['users.id']),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 16. Class Polls
    op.create_table(
        'class_polls',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('class_group_id', sa.UUID(), nullable=False),
        sa.Column('question', sa.String(length=300), nullable=False),
        sa.Column('is_closed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'class_poll_options',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('poll_id', sa.UUID(), nullable=False),
        sa.Column('option_text', sa.String(length=200), nullable=False),
        sa.Column('vote_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['poll_id'], ['class_polls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'class_poll_votes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('poll_id', sa.UUID(), nullable=False),
        sa.Column('option_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('voted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['option_id'], ['class_poll_options.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['poll_id'], ['class_polls.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('poll_id', 'user_id', name='uq_class_poll_user_vote')
    )

    # 17. Class Events
    op.create_table(
        'class_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('class_group_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False, server_default='EVENT'),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['class_group_id'], ['class_groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 18. Organizations & Publications
    op.create_table(
        'organizations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('owner_user_id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    op.create_table(
        'publications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('author_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('media_urls', sa.JSON(), nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=False),
        sa.Column('is_sponsored', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('views_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 19. Ad System
    op.create_table(
        'ad_campaigns',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('advertiser_name', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('starts_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('target_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'ad_creatives',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('campaign_id', sa.UUID(), nullable=False),
        sa.Column('headline', sa.String(length=200), nullable=False),
        sa.Column('body_text', sa.Text(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('cta_text', sa.String(length=100), nullable=False, server_default='En savoir plus'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['ad_campaigns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'ad_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creative_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('ip', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['creative_id'], ['ad_creatives.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 20. Audit Log
    op.create_table(
        'audit_log',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('ad_events')
    op.drop_table('ad_creatives')
    op.drop_table('ad_campaigns')
    op.drop_table('publications')
    op.drop_table('organizations')
    op.drop_table('class_events')
    op.drop_table('class_poll_votes')
    op.drop_table('class_poll_options')
    op.drop_table('class_polls')
    op.drop_table('class_incidents')
    op.drop_table('class_announcements')
    op.drop_table('room_status_declarations')
    op.drop_table('rooms')
    op.drop_table('certification_documents')
    op.drop_table('class_delegates')
    op.drop_table('enrollment_attempts')
    op.drop_table('invitations')
    op.drop_table('memberships')
    op.drop_table('roster_entries')
    op.drop_table('import_batches')
    op.drop_table('class_groups')
    op.drop_table('tenant_subscriptions')
    op.drop_table('tenants')
    op.drop_table('users')
