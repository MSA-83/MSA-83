"""Initial migration - create all tables.

Revision ID: 001_initial
Revises:
Create Date: 2026-05-07
"""

import sqlalchemy as sa
from alembic import op

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("tier", sa.String(20), server_default="free"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("is_verified", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_login", sa.DateTime, nullable=True),
    )

    op.create_table(
        "user_usage",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("queries_this_month", sa.Integer, server_default="0"),
        sa.Column("documents_stored", sa.Integer, server_default="0"),
        sa.Column("active_agents", sa.Integer, server_default="0"),
        sa.Column("tokens_used", sa.Integer, server_default="0"),
        sa.Column("month", sa.String(7), nullable=False),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("source", sa.String(500), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("file_type", sa.String(50), nullable=True),
        sa.Column("chunker_strategy", sa.String(50), server_default="fixed"),
        sa.Column("chunks_processed", sa.Integer, server_default="0"),
        sa.Column("chunks_stored", sa.Integer, server_default="0"),
        sa.Column("char_count", sa.Integer, server_default="0"),
        sa.Column("word_count", sa.Integer, server_default="0"),
        sa.Column("metadata", sa.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("task_description", sa.Text, nullable=False),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("priority", sa.String(20), server_default="normal"),
        sa.Column("result", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("execution_time_ms", sa.Integer, nullable=True),
        sa.Column("tokens_used", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("tier", sa.String(50), nullable=False),
        sa.Column("billing_cycle", sa.String(20), server_default="monthly"),
        sa.Column("amount", sa.Integer, server_default="0"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("current_period_start", sa.DateTime, nullable=True),
        sa.Column("current_period_end", sa.DateTime, nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("tasks")
    op.drop_table("documents")
    op.drop_table("user_usage")
    op.drop_table("users")
