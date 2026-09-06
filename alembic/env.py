# backend/alembic/env.py

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Imports pour la configuration et les métadonnées
from shared_kernel.config import settings
from shared_kernel.infrastructure.database import Base

# Import de tous les modèles pour que target_metadata soit complet
import identity_context.infrastructure.persistence.models
import community_context.infrastructure.persistence.models
import democracy_context.infrastructure.persistence.models
import academy_context.infrastructure.persistence.models
import campus_life_context.infrastructure.persistence.models
import opportunities_context.infrastructure.persistence.models
import monetization_context.infrastructure.persistence.models
import trust_safety_context.infrastructure.persistence.models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Métadonnées cibles pour l'autogénération
target_metadata = Base.metadata


def get_url() -> str:
    """Retourne l'URL de la base de données depuis la configuration centrale."""
    return settings.DATABASE_URL


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


def do_run_migrations(connection: Connection) -> None:
    """Exécute les migrations sur une connexion synchrone."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Crée un moteur asynchrone et exécute les migrations."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = create_async_engine(
        get_url(),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()