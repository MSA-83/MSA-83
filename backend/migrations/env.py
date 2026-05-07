"""Alembic configuration for Titanium platform."""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from backend.models.database import Base

# Import all models so Alembic can detect them
from backend.models.user import User, UserUsage
from backend.models.document import Document
from backend.models.task import Task
from backend.models.subscription import Subscription
from backend.models.analytics_event import AnalyticsEvent
from backend.models.audit_log import AuditLog

target_metadata = Base.metadata


def get_url():
    return os.getenv(
        "DATABASE_URL",
        "sqlite:///./titanium.db",
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
