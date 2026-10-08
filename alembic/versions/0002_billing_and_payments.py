"""0002 billing and payments tables

Revision ID: 0002_billing_and_payments
Revises: 0001_baseline
Create Date: 2026-10-07 02:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_billing_and_payments'
down_revision: Union[str, None] = '0001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table plans
    op.create_table(
        'plans',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('price_xaf', sa.BigInteger(), nullable=False),
        sa.Column('billing_period', sa.String(length=50), server_default='ACADEMIC_YEAR', nullable=False),
        sa.Column('seats_included', sa.Integer(), server_default='1000', nullable=False),
        sa.Column('extra_seat_price_xaf', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('trial_days', sa.Integer(), server_default='14', nullable=False),
        sa.Column('features_json', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code', name='uq_plan_code')
    )
    op.create_index('idx_plans_code', 'plans', ['code'])

    # 2. Table invoices
    op.create_table(
        'invoices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('number', sa.String(length=100), nullable=False),
        sa.Column('academic_year', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='DRAFT', nullable=False),
        sa.Column('subtotal_xaf', sa.BigInteger(), nullable=False),
        sa.Column('tax_rate_percent', sa.Integer(), server_default='0', nullable=False),
        sa.Column('tax_xaf', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('total_xaf', sa.BigInteger(), nullable=False),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pdf_url', sa.String(length=500), nullable=True),
        sa.Column('billing_contact_email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'number', name='uq_invoice_number_per_tenant')
    )
    op.create_index('idx_invoice_tenant_status', 'invoices', ['tenant_id', 'status'])

    # 3. Table invoice_lines
    op.create_table(
        'invoice_lines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('invoice_id', sa.UUID(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1', nullable=False),
        sa.Column('unit_price_xaf', sa.BigInteger(), nullable=False),
        sa.Column('total_xaf', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_invoice_line_invoice_id', 'invoice_lines', ['invoice_id'])

    # 4. Table payments
    op.create_table(
        'payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('invoice_id', sa.UUID(), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('provider_ref', sa.String(length=255), nullable=True),
        sa.Column('amount_xaf', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='XAF', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('phone_number_masked', sa.String(length=50), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_payment_tenant_status', 'payments', ['tenant_id', 'status'])
    op.create_index('idx_payment_provider_ref', 'payments', ['provider_ref'])

    # 5. Table payment_attempts
    op.create_table(
        'payment_attempts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('invoice_id', sa.UUID(), nullable=False),
        sa.Column('amount_xaf', sa.BigInteger(), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('provider_ref', sa.String(length=255), nullable=True),
        sa.Column('phone_number_masked', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_payment_attempt_provider_ref', 'payment_attempts', ['provider_ref'])

    # 6. Table payment_events
    op.create_table(
        'payment_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('provider_event_id', sa.String(length=255), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=False),
        sa.Column('is_signature_valid', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_name', 'provider_event_id', name='uq_payment_event_provider_id')
    )

    # 7. Table manual_payment_proofs
    op.create_table(
        'manual_payment_proofs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('invoice_id', sa.UUID(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('payment_reference', sa.String(length=255), nullable=True),
        sa.Column('amount_declared_xaf', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='SUBMITTED', nullable=False),
        sa.Column('reviewed_by_user_id', sa.UUID(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. Table credit_notes
    op.create_table(
        'credit_notes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('invoice_id', sa.UUID(), nullable=False),
        sa.Column('number', sa.String(length=100), nullable=False),
        sa.Column('amount_xaf', sa.BigInteger(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('number', name='uq_credit_note_number')
    )

    # 9. Table dunning_events
    op.create_table(
        'dunning_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('subscription_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('sent_to_email', sa.String(length=255), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['subscription_id'], ['tenant_subscriptions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_dunning_tenant_event', 'dunning_events', ['tenant_id', 'event_type'])

    # 10. Table billing_settings
    op.create_table(
        'billing_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tax_rate_percent', sa.Integer(), server_default='0', nullable=False),
        sa.Column('tax_id_number', sa.String(length=100), nullable=True),
        sa.Column('company_name', sa.String(length=255), server_default='Pineapple OS SARL', nullable=False),
        sa.Column('company_address', sa.Text(), server_default='Douala, Cameroun', nullable=False),
        sa.Column('legal_notice', sa.Text(), server_default='Facture payable en XAF FCFA. Sous réserve de validation comptable.', nullable=False),
        sa.Column('default_grace_days', sa.Integer(), server_default='7', nullable=False),
        sa.Column('default_trial_days', sa.Integer(), server_default='14', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('billing_settings')
    op.drop_index('idx_dunning_tenant_event', table_name='dunning_events')
    op.drop_table('dunning_events')
    op.drop_table('credit_notes')
    op.drop_table('manual_payment_proofs')
    op.drop_table('payment_events')
    op.drop_table('payment_attempts')
    op.drop_index('idx_payment_provider_ref', table_name='payments')
    op.drop_index('idx_payment_tenant_status', table_name='payments')
    op.drop_table('payments')
    op.drop_index('idx_invoice_line_invoice_id', table_name='invoice_lines')
    op.drop_table('invoice_lines')
    op.drop_index('idx_invoice_tenant_status', table_name='invoices')
    op.drop_table('invoices')
    op.drop_index('idx_plans_code', table_name='plans')
    op.drop_table('plans')
