"""0005 regie publicitaire visiteurs tables

Revision ID: 0005_regie_publicitaire_visiteurs
Revises: 0004_notifications_multicanal
Create Date: 2026-10-08 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005_regie_publicitaire_visiteurs'
down_revision: Union[str, None] = '0004_notifications_multicanal'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. advertisers
    op.create_table(
        'advertisers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=100), server_default='CM', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. advertiser_users
    op.create_table(
        'advertiser_users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('advertiser_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='ADVERTISER', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['advertiser_id'], ['advertisers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('advertiser_id', 'user_id', name='uq_advertiser_user')
    )
    op.create_index(op.f('ix_advertiser_users_advertiser_id'), 'advertiser_users', ['advertiser_id'], unique=False)
    op.create_index(op.f('ix_advertiser_users_user_id'), 'advertiser_users', ['user_id'], unique=False)

    # 3. ad_wallets
    op.create_table(
        'ad_wallets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('advertiser_id', sa.UUID(), nullable=False),
        sa.Column('balance_xaf', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['advertiser_id'], ['advertisers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('advertiser_id', name='uq_ad_wallets_advertiser_id')
    )
    op.create_index(op.f('ix_ad_wallets_advertiser_id'), 'ad_wallets', ['advertiser_id'], unique=True)

    # 4. wallet_transactions
    op.create_table(
        'wallet_transactions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('wallet_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('amount_xaf', sa.BigInteger(), nullable=False),
        sa.Column('balance_after_xaf', sa.BigInteger(), nullable=False),
        sa.Column('reference_id', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['wallet_id'], ['ad_wallets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wallet_transactions_wallet_id'), 'wallet_transactions', ['wallet_id'], unique=False)

    # 5. ad_targeting_rules
    op.create_table(
        'ad_targeting_rules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('campaign_id', sa.UUID(), nullable=False),
        sa.Column('cities_regions_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('languages_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('device_types_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('hours_of_day_json', sa.Text(), server_default='[]', nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['ad_campaigns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', name='uq_ad_targeting_rules_campaign_id')
    )
    op.create_index(op.f('ix_ad_targeting_rules_campaign_id'), 'ad_targeting_rules', ['campaign_id'], unique=True)

    # 6. ad_review_events
    op.create_table(
        'ad_review_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creative_id', sa.UUID(), nullable=False),
        sa.Column('reviewer_user_id', sa.UUID(), nullable=True),
        sa.Column('previous_status', sa.String(length=50), nullable=False),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['creative_id'], ['ad_creatives.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ad_review_events_creative_id'), 'ad_review_events', ['creative_id'], unique=False)

    # 7. ad_impressions_raw
    op.create_table(
        'ad_impressions_raw',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creative_id', sa.UUID(), nullable=False),
        sa.Column('campaign_id', sa.UUID(), nullable=False),
        sa.Column('visitor_session_id', sa.String(length=100), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('ip', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['ad_campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['creative_id'], ['ad_creatives.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token', name='uq_ad_impressions_raw_token')
    )
    op.create_index(op.f('ix_ad_impressions_raw_campaign_id'), 'ad_impressions_raw', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_ad_impressions_raw_creative_id'), 'ad_impressions_raw', ['creative_id'], unique=False)
    op.create_index(op.f('ix_ad_impressions_raw_token'), 'ad_impressions_raw', ['token'], unique=True)
    op.create_index(op.f('ix_ad_impressions_raw_visitor_session_id'), 'ad_impressions_raw', ['visitor_session_id'], unique=False)

    # 8. ad_stats_daily
    op.create_table(
        'ad_stats_daily',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('campaign_id', sa.UUID(), nullable=False),
        sa.Column('creative_id', sa.UUID(), nullable=False),
        sa.Column('stat_date', sa.String(length=10), nullable=False),
        sa.Column('impressions_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('clicks_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('spent_xaf', sa.BigInteger(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['ad_campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['creative_id'], ['ad_creatives.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', 'creative_id', 'stat_date', name='uq_ad_stats_daily_cmp_crt_date')
    )
    op.create_index(op.f('ix_ad_stats_daily_campaign_id'), 'ad_stats_daily', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_ad_stats_daily_creative_id'), 'ad_stats_daily', ['creative_id'], unique=False)
    op.create_index(op.f('ix_ad_stats_daily_stat_date'), 'ad_stats_daily', ['stat_date'], unique=False)

    # 9. ad_user_feedback
    op.create_table(
        'ad_user_feedback',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('creative_id', sa.UUID(), nullable=False),
        sa.Column('visitor_session_id', sa.String(length=100), nullable=False),
        sa.Column('feedback_type', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.String(length=100), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['creative_id'], ['ad_creatives.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ad_user_feedback_creative_id'), 'ad_user_feedback', ['creative_id'], unique=False)
    op.create_index(op.f('ix_ad_user_feedback_visitor_session_id'), 'ad_user_feedback', ['visitor_session_id'], unique=False)

    # 10. ad_policy_rules
    op.create_table(
        'ad_policy_rules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('forbidden_keywords_json', sa.Text(), server_default='[]', nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category', name='uq_ad_policy_rules_category')
    )
    op.create_index(op.f('ix_policy_rules_category'), 'ad_policy_rules', ['category'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_policy_rules_category'), table_name='ad_policy_rules')
    op.drop_table('ad_policy_rules')

    op.drop_index(op.f('ix_ad_user_feedback_visitor_session_id'), table_name='ad_user_feedback')
    op.drop_index(op.f('ix_ad_user_feedback_creative_id'), table_name='ad_user_feedback')
    op.drop_table('ad_user_feedback')

    op.drop_index(op.f('ix_ad_stats_daily_stat_date'), table_name='ad_stats_daily')
    op.drop_index(op.f('ix_ad_stats_daily_creative_id'), table_name='ad_stats_daily')
    op.drop_index(op.f('ix_ad_stats_daily_campaign_id'), table_name='ad_stats_daily')
    op.drop_table('ad_stats_daily')

    op.drop_index(op.f('ix_ad_impressions_raw_visitor_session_id'), table_name='ad_impressions_raw')
    op.drop_index(op.f('ix_ad_impressions_raw_token'), table_name='ad_impressions_raw')
    op.drop_index(op.f('ix_ad_impressions_raw_creative_id'), table_name='ad_impressions_raw')
    op.drop_index(op.f('ix_ad_impressions_raw_campaign_id'), table_name='ad_impressions_raw')
    op.drop_table('ad_impressions_raw')

    op.drop_index(op.f('ix_ad_review_events_creative_id'), table_name='ad_review_events')
    op.drop_table('ad_review_events')

    op.drop_index(op.f('ix_ad_targeting_rules_campaign_id'), table_name='ad_targeting_rules')
    op.drop_table('ad_targeting_rules')

    op.drop_index(op.f('ix_wallet_transactions_wallet_id'), table_name='wallet_transactions')
    op.drop_table('wallet_transactions')

    op.drop_index(op.f('ix_ad_wallets_advertiser_id'), table_name='ad_wallets')
    op.drop_table('ad_wallets')

    op.drop_index(op.f('ix_advertiser_users_user_id'), table_name='advertiser_users')
    op.drop_index(op.f('ix_advertiser_users_advertiser_id'), table_name='advertiser_users')
    op.drop_table('advertiser_users')

    op.drop_table('advertisers')
