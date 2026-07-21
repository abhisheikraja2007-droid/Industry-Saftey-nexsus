"""Alembic environment — async SQLAlchemy with DATABASE_URL from environment."""
from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# ----- Alembic Config -----
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ----- Import metadata from all models -----
# This ensures all models are registered so Alembic can autogenerate migrations.
from models.db_models import Base  # noqa: F401 — imports all business models
from models.user import UserModel, TokenBlacklist  # noqa: F401 — imports auth models

target_metadata = Base.metadata

# ----- Override URL from environment -----
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://safety_user:safety_pass@postgres:5432/safety_db"
)
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection required)."""
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


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode (with async DB connection)."""
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
