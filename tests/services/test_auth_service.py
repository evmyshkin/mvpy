"""Тесты для AuthService."""

from datetime import UTC
from datetime import datetime

import pytest

from faker import Faker
from fastapi import HTTPException
from jose import jwt
from sqlalchemy import select
from starlette.status import HTTP_401_UNAUTHORIZED

from app.api.utils.enums.auth import AuthErrorMessage
from app.api.v1.schemas.auth import AuthRequest
from app.api.v1.schemas.auth import AuthResponse
from app.api.v1.schemas.users import UserCreateRequest
from app.config import config
from app.db.models.user import User
from app.services.auth_service import AuthService
from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_authenticate_success(db_session, faker: Faker) -> None:
    """Тест успешной аутентификации."""
    # Создаем пользователя
    service = UserService()
    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
    )
    user = await service.create_user(session=db_session, user_data=user_request)

    # Аутентифицируемся
    auth_service = AuthService()
    auth_request = AuthRequest(
        email=user_request.email,
        password='Password123',
    )
    response = await auth_service.authenticate(session=db_session, auth_data=auth_request)

    # Проверяем ответ
    assert isinstance(response, AuthResponse)
    assert response.access_token is not None
    assert response.token_type == 'bearer'
    assert response.expires_in == config.jwt.access_token_expire_minutes * 60

    # Проверяем JWT токен
    payload = jwt.decode(
        response.access_token, config.jwt.secret_key, algorithms=[config.jwt.algorithm]
    )
    assert payload['user_id'] == user.id
    assert payload['is_active'] is True
    assert 'exp' in payload
    assert 'iat' in payload
    assert 'jti' in payload


@pytest.mark.asyncio
async def test_authenticate_user_not_found(db_session, faker: Faker) -> None:
    """Тест аутентификации с несуществующим email."""
    auth_service = AuthService()
    auth_request = AuthRequest(
        email='nonexistent@example.com',
        password='Password123',
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate(session=db_session, auth_data=auth_request)

    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == AuthErrorMessage.INVALID_CREDENTIALS


@pytest.mark.asyncio
async def test_authenticate_wrong_password(db_session, faker: Faker) -> None:
    """Тест аутентификации с неверным паролем."""
    # Создаем пользователя
    service = UserService()
    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
    )
    await service.create_user(session=db_session, user_data=user_request)

    # Пытаемся аутентифицироваться с неверным паролем
    auth_service = AuthService()
    auth_request = AuthRequest(
        email=user_request.email,
        password='WrongPassword456',
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate(session=db_session, auth_data=auth_request)

    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == AuthErrorMessage.INVALID_CREDENTIALS


@pytest.mark.asyncio
async def test_authenticate_inactive_user(db_session, faker: Faker) -> None:
    """Тест аутентификации неактивного пользователя."""
    # Создаем и деактивируем пользователя
    service = UserService()
    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
    )
    user = await service.create_user(session=db_session, user_data=user_request)

    # Деактивируем пользователя напрямую через модель
    result = await db_session.execute(select(User).where(User.id == user.id))
    user_model = result.scalars().first()
    user_model.is_active = False
    await db_session.commit()

    # Пытаемся аутентифицироваться
    auth_service = AuthService()
    auth_request = AuthRequest(
        email=user_request.email,
        password='Password123',
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_service.authenticate(session=db_session, auth_data=auth_request)

    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == AuthErrorMessage.INACTIVE_USER


@pytest.mark.asyncio
async def test_logout_success(db_session, faker: Faker) -> None:
    """Тест успешного выхода из системы."""
    # Создаем пользователя и аутентифицируемся
    user_service = UserService()
    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
    )
    user = await user_service.create_user(session=db_session, user_data=user_request)

    auth_service = AuthService()
    auth_request = AuthRequest(
        email=user_request.email,
        password='Password123',
    )
    auth_response = await auth_service.authenticate(session=db_session, auth_data=auth_request)

    # Декодируем токен для получения jti и exp
    payload = jwt.decode(
        auth_response.access_token, config.jwt.secret_key, algorithms=[config.jwt.algorithm]
    )
    token_jti = payload['jti']
    # Конвертируем в naive datetime для PostgreSQL
    token_expires_aware = datetime.fromtimestamp(payload['exp'], tz=UTC)
    token_expires_at = token_expires_aware.replace(tzinfo=None)

    # Выполняем logout
    logout_response = await auth_service.logout(
        session=db_session,
        token_jti=token_jti,
        user_id=user.id,
        token_expires_at=token_expires_at,
    )

    # Проверяем ответ
    assert logout_response.message == AuthErrorMessage.LOGOUT_SUCCESS

    # Проверяем, что токен в черном списке
    from app.db.crud.blacklisted_tokens import BlacklistedTokenCrud

    blacklist_crud = BlacklistedTokenCrud()
    blacklisted_token = await blacklist_crud.find_one_or_none(
        db_session,
        token_jti=token_jti,
    )
    assert blacklisted_token is not None
    assert blacklisted_token.user_id == user.id


@pytest.mark.asyncio
async def test_logout_token_already_blacklisted(db_session, faker: Faker) -> None:
    """Тест повтора logout с тем же токеном."""
    # Создаем пользователя и аутентифицируемся
    user_service = UserService()
    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
    )
    user = await user_service.create_user(session=db_session, user_data=user_request)

    auth_service = AuthService()
    auth_request = AuthRequest(
        email=user_request.email,
        password='Password123',
    )
    auth_response = await auth_service.authenticate(session=db_session, auth_data=auth_request)

    # Декодируем токен для получения jti и exp
    payload = jwt.decode(
        auth_response.access_token, config.jwt.secret_key, algorithms=[config.jwt.algorithm]
    )
    token_jti = payload['jti']
    # Конвертируем в naive datetime для PostgreSQL
    token_expires_aware = datetime.fromtimestamp(payload['exp'], tz=UTC)
    token_expires_at = token_expires_aware.replace(tzinfo=None)

    # Первый logout
    await auth_service.logout(
        session=db_session,
        token_jti=token_jti,
        user_id=user.id,
        token_expires_at=token_expires_at,
    )

    # Пытаемся logout с тем же токеном
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.logout(
            session=db_session,
            token_jti=token_jti,
            user_id=user.id,
            token_expires_at=token_expires_at,
        )

    assert exc_info.value.status_code == HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == AuthErrorMessage.TOKEN_ALREADY_BLACKLISTED
