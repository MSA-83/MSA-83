"""add stripe_events table

Revision ID: a1b2c3d4e5f6
Revises: 711b6cbebed4
Create Date: 2026-05-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '711b6cbebed4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'stripe_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('stripe_event_id', sa.String(100), unique=True, nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('customer_id', sa.String(100), nullable=True),
        sa.Column('user_id', sa.String(36), nullable=True),
        sa.Column('subscription_id', sa.String(100), nullable=True),
        sa.Column('invoice_id', sa.String(100), nullable=True),
        sa.Column('amount', sa.Integer, nullable=True),
        sa.Column('currency', sa.String(3), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='received'),
        sa.Column('payload', sa.JSON, nullable=False, server_default='{}'),
        sa.Column('processed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_stripe_events_stripe_event_id', 'stripe_events', ['stripe_event_id'])
    op.create_index('ix_stripe_events_event_type', 'stripe_events', ['event_type'])
    op.create_index('ix_stripe_events_customer_id', 'stripe_events', ['customer_id'])
    op.create_index('ix_stripe_events_user_id', 'stripe_events', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_stripe_events_user_id')
    op.drop_index('ix_stripe_events_customer_id')
    op.drop_index('ix_stripe_events_event_type')
    op.drop_index('ix_stripe_events_stripe_event_id')
    op.drop_table('stripe_events')
