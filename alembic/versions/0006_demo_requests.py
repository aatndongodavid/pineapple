"""demo requests table

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-08 02:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'demo_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('institution_name', sa.String(length=255), nullable=False),
        sa.Column('contact_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('whatsapp_phone', sa.String(length=100), nullable=False),
        sa.Column('student_count_range', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='NEW', nullable=False),
        sa.Column('ip_address', sa.String(length=100), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_demo_requests_created_at', 'demo_requests', ['created_at'])
    op.create_index('ix_demo_requests_status', 'demo_requests', ['status'])
    op.create_index('ix_demo_requests_email', 'demo_requests', ['email'])


def downgrade() -> None:
    op.drop_index('ix_demo_requests_email', table_name='demo_requests')
    op.drop_index('ix_demo_requests_status', table_name='demo_requests')
    op.drop_index('ix_demo_requests_created_at', table_name='demo_requests')
    op.drop_table('demo_requests')
