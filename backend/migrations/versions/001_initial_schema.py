"""Initial Pineapple Database Schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-16 22:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tenants Table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('logo_url', sa.String(length=512), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_tenants_code'), 'tenants', ['code'], unique=True)

    # 2. Users Table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('account_status', sa.Enum('ACCOUNT', 'VERIFICATION_PENDING', 'VERIFIED', 'REJECTED', name='accountstatus'), nullable=False, server_default='ACCOUNT'),
        sa.Column('academic_status', sa.Enum('STUDENT', 'TEACHER', 'ALUMNI', 'ADMIN', name='academicstatus'), nullable=False, server_default='STUDENT'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_users_tenant_id'), 'users', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 3. Certification Requests Table
    op.create_table(
        'certification_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id_number', sa.String(length=100), nullable=False),
        sa.Column('document_url', sa.String(length=512), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='certificationstatus'), nullable=False, server_default='PENDING'),
        sa.Column('rejection_reason', sa.String(length=512), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_certification_requests_user_id'), 'certification_requests', ['user_id'], unique=False)

    # 4. Posts Table
    op.create_table(
        'posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum('ACTU', 'RECHERCHE', 'VIE_ETUDIANTE', name='postcategory'), nullable=False, server_default='ACTU'),
        sa.Column('is_sponsored', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('media_urls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_posts_tenant_id'), 'posts', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_posts_author_id'), 'posts', ['author_id'], unique=False)

    # 5. Comments Table
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_comments_post_id'), 'comments', ['post_id'], unique=False)
    op.create_index(op.f('ix_comments_author_id'), 'comments', ['author_id'], unique=False)

    # 6. Reactions Table
    op.create_table(
        'reactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reaction_type', sa.Enum('LIKE', 'LOVE', 'SUPPORT', name='reactiontype'), nullable=False, server_default='LIKE'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('post_id', 'user_id', name='uq_post_user_reaction')
    )
    op.create_index(op.f('ix_reactions_post_id'), 'reactions', ['post_id'], unique=False)
    op.create_index(op.f('ix_reactions_user_id'), 'reactions', ['user_id'], unique=False)

    # 7. Elections Table
    op.create_table(
        'elections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'UPCOMING', 'OPEN', 'CLOSED', 'ARCHIVED', name='electionstatus'), nullable=False, server_default='DRAFT'),
        sa.Column('eligibility_rules', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_elections_tenant_id'), 'elections', ['tenant_id'], unique=False)

    # 8. Encrypted Ballots Table
    op.create_table(
        'encrypted_ballots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('election_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('elections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('voter_hash', sa.String(length=255), nullable=False),
        sa.Column('encrypted_vote_payload', sa.String(length=1024), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_encrypted_ballots_election_id'), 'encrypted_ballots', ['election_id'], unique=False)
    op.create_index(op.f('ix_encrypted_ballots_voter_hash'), 'encrypted_ballots', ['voter_hash'], unique=False)

    # 9. Audit Logs Table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_audit_logs_tenant_id'), 'audit_logs', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('encrypted_ballots')
    op.drop_table('elections')
    op.drop_table('reactions')
    op.drop_table('comments')
    op.drop_table('posts')
    op.drop_table('certification_requests')
    op.drop_table('users')
    op.drop_table('tenants')
    
    op.execute('DROP TYPE IF EXISTS accountstatus')
    op.execute('DROP TYPE IF EXISTS academicstatus')
    op.execute('DROP TYPE IF EXISTS certificationstatus')
    op.execute('DROP TYPE IF EXISTS postcategory')
    op.execute('DROP TYPE IF EXISTS reactiontype')
    op.execute('DROP TYPE IF EXISTS electionstatus')
