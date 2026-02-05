"""Fixtures для тестирования."""

import asyncio

from collections.abc import AsyncGenerator
from collections.abc import Generator

import pytest
import pytest_asyncio

from faker import Faker
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.v1.schemas.users import UserCreateRequest
from app.api.v1.schemas.users import UserUpdateRequest
from app.config import config
from app.db.base import BaseDBModel
from app.db.session import DBConnector
from app.main import app
from app.services.user_service import UserService


@pytest.fixture(scope='session')
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """Создать event loop для асинхронных тестов.

    Yields:
        Event loop
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def faker() -> Faker:
    """Генератор тестовых данных.

    Returns:
        Экземпляр Faker
    """
    return Faker()


@pytest_asyncio.fixture(scope='session')
async def test_db_engine():
    """Создать тестовый движок БД для PYTEST окружения.

    Yields:
        Тестовый движок БД
    """
    # Устанавливаем окружение PYTEST для использования test_database_uri
    import os

    os.environ['APP__ENVIRONMENT'] = 'PYTEST'

    # Пересоздаем config с PYTEST окружением
    from app.config import Settings

    test_config = Settings()
    test_database_url = test_config.postgres.test_database_uri

    engine = create_async_engine(test_database_url, echo=False)

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession]:
    """Создать асинхронную сессию БД для тестов.

    Args:
        test_db_engine: Тестовый движок БД

    Yields:
        Асинхронная сессия БД
    """
    async_session_maker = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    # Начинаем транзакцию на уровне фикстуры
    async with async_session_maker() as session, session.begin():  # Начинаем транзакцию здесь
        yield session  # Передаем сессию в тест
        # Откат после теста
        await session.rollback()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Создать асинхронный HTTP клиент для тестирования FastAPI.

    Args:
        db_session: Асинхронная сессия БД

    Yields:
        Асинхронный HTTP клиент с base_url из config
    """
    # Создаем тестовый connector
    test_connector = DBConnector(db_url=config.postgres.test_database_uri)

    # Подменяем зависимость сессии БД на тестовую
    async def override_get_session():
        yield db_session

    app.dependency_overrides[test_connector.get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=config.app.test_api_base_url) as client:
        yield client

    # Удаляем override
    app.dependency_overrides.clear()


@pytest.fixture
def valid_user_request(faker: Faker) -> UserCreateRequest:
    """Валидный запрос на создание пользователя.

    Args:
        faker: Генератор тестовых данных

    Returns:
        Pydantic схема UserCreateRequest с валидными данными
    """
    return UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
    )


@pytest.fixture
def user_service(db_session: AsyncSession) -> UserService:
    """Fixture для UserService с тестовой сессией БД.

    Args:
        db_session: Тестовая сессия БД

    Returns:
        Экземпляр UserService, готовый к использованию с db_session
    """
    return UserService()


@pytest.fixture
def update_user_request(faker: Faker) -> UserUpdateRequest:
    """Валидный запрос на обновление пользователя.

    Args:
        faker: Генератор тестовых данных

    Returns:
        Pydantic схема UserUpdateRequest с валидными данными
    """
    return UserUpdateRequest(
        email=faker.email(),
        first_name='Пётр',
        last_name='Петров',
        password='NewPassword456',
    )
