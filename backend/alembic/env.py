# alembic/env.py
# Alembic migration environment configured for CampusHire.
#
# Key behaviours:
#   - DATABASE_URL is loaded from .env via app.core.config.settings
#   - All models are imported so autogenerate sees every table
#   - Supports both offline and online migration modes

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ---------------------------------------------------------------------------
# Make sure the project root is on sys.path so `app.*` imports resolve.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Import settings — loads DATABASE_URL from .env
# ---------------------------------------------------------------------------
from app.core.config import settings  # noqa: E402

# ---------------------------------------------------------------------------
# Import Base and ALL models so autogenerate detects every table.
# ---------------------------------------------------------------------------
from app.database.base import Base  # noqa: E402
import app.models  # noqa: E402, F401  # side-effect: registers all mappers

# ---------------------------------------------------------------------------
# Alembic Config object — gives access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Override sqlalchemy.url with the value from .env
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode — generates SQL without connecting to a live DB
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations without a live database connection.

    Useful for generating plain SQL scripts to run manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — connects to the database and applies migrations
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
