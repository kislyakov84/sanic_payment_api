import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# --- ЭТО НУЖНО СДЕЛАТЬ ДО ИМПОРТА НАШИХ МОДУЛЕЙ ---
# Добавляем путь к корневой папке проекта (где лежит .env, alembic.ini)
# чтобы Alembic мог найти src/models/tables.py и src/core/config.py
sys.path.insert(
    0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
)

# --- А ТЕПЕРЬ ВСЕ ОСТАЛЬНЫЕ ИМПОРТЫ ---
from src.core.config import settings
from src.models.tables import Base

# --- И ТОЛЬКО ПОТОМ ОСТАЛЬНОЙ КОД ---
load_dotenv()  # Загружаем переменные окружения из .env

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Теперь Alembic знает о наших таблицах
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.database_url_asyncpg.replace("+asyncpg", "")
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
    alembic_config = config.get_section(config.config_ini_section)

    if alembic_config is None:
        raise RuntimeError("Alembic configuration section not found in config file.")

    alembic_config["sqlalchemy.url"] = settings.database_url_asyncpg.replace(
        "+asyncpg", ""
    )

    connectable = engine_from_config(
        alembic_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
