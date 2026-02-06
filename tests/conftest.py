"""Fixtures для тестирования."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from faker import Faker
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.api.v1.schemas.users import UserCreateRequest
from app.api.v1.schemas.users import UserCreateResponse
from app.api.v1.schemas.users import UserUpdateRequest
from app.config import config
from app.db.base import BaseDBModel
from app.db.session import DBConnector
from app.main import app
from app.services.user_service import UserService


@pytest.fixture(scope='session')
def faker() -> Faker:
    """Генератор тестовых данных.

    Returns:
        Экземпляр Faker
    """
    return Faker()


@pytest_asyncio.fixture
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

    engine = create_async_engine(
        test_database_url,
        echo=False,
        poolclass=NullPool,
    )

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(BaseDBModel.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession]:
    """Создать асинхронную сессию БД для тестов с очисткой через TRUNCATE.

    TRUNCATE используется вместо rollback, так как CRUD методы выполняют
    реальный commit() в базу данных.

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

    session = async_session_maker()

    # Очистка перед тестом
    async with test_db_engine.begin() as conn:
        for table in BaseDBModel.metadata.sorted_tables:
            await conn.execute(text(f'TRUNCATE TABLE {table.name} CASCADE'))

    try:
        yield session
    finally:
        # Закрываем сессию
        await session.close()
        # Очистка после теста, чтобы в БД не оставалось данных
        async with test_db_engine.begin() as conn:
            for table in BaseDBModel.metadata.sorted_tables:
                await conn.execute(text(f'TRUNCATE TABLE {table.name} CASCADE'))


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


@pytest_asyncio.fixture
async def user_service(db_session: AsyncSession) -> UserService:
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


@pytest_asyncio.fixture
async def existing_user(db_session: AsyncSession, faker: Faker) -> UserCreateResponse:
    """Создать существующего пользователя в БД для тестов обновления.

    Args:
        db_session: Тестовая сессия БД
        faker: Генератор тестовых данных

    Returns:
        Созданный пользователь (UserCreateResponse)
    """
    service = UserService()

    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
    )

    user = await service.create_user(session=db_session, user_data=user_request)

    return UserCreateResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )
