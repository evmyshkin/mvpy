"""Alembic окружение для миграций БД."""

import asyncio

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.api.utils.enums.env_enum import EnvEnum
from app.config import config as app_config

# Импортируем Base, чтобы зарегистрировать все модели
from app.db.base import BaseDBModel

sqlalchemy_url = (
    app_config.postgres.test_database_uri + '/test_migrations'
    if app_config.app.environment == EnvEnum.PYTEST
    else app_config.postgres.database_uri
)

config = context.config

# Устанавливаем URL БД из настроек
config.set_main_option('sqlalchemy.url', sqlalchemy_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для автоматического создания миграций
target_metadata = BaseDBModel.metadata


def run_migrations_offline() -> None:
    """Запустить миграции в offline режиме.

    В этом режиме не нужно подключаться к БД.
    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        include_schemas=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Выполнить миграции в online режиме.

    Args:
        connection: SQLAlchemy connection.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Запустить асинхронные миграции."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Запустить миграции в online режиме (с подключением к БД)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
