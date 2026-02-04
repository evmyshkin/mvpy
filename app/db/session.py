"""Асинхронное подключение к PostgreSQL."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.utils.enums.env_enum import EnvEnum
from app.config import config


class DBConnector:
    def __init__(self, db_url: str | None = None) -> None:
        """Инициализируем объект коннектора.

        Args:
            db_url: str - строка подключения к БД.
        """

        if db_url:
            self.db_url = db_url
        elif config.app.environment == EnvEnum.PYTEST:
            self.db_url = config.postgres.test_database_uri
        else:
            self.db_url = config.postgres.database_uri

    def get_db_engine(self, db_url: str) -> AsyncEngine:
        """Создать движок подключения к Postgres."""
        engine = create_async_engine(url=db_url)
        return engine

    def get_session_maker(self) -> async_sessionmaker:
        """Создать фабрику асинхронных сессий."""
        return async_sessionmaker(
            bind=self.get_db_engine(db_url=self.db_url),
            expire_on_commit=False,
            autoflush=False,
        )

    async def get_session(self) -> AsyncGenerator:
        """Получить сессию БД для dependency injection.

        Yields:
            Асинхронная сессия SQLAlchemy.
        """
        session_maker = self.get_session_maker()

        async with session_maker() as db:
            yield db


connector = DBConnector()
