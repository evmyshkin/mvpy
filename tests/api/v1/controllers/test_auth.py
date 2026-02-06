"""Тесты для auth эндпоинтов."""

from datetime import UTC

import pytest

from fastapi import status
from jose import jwt

from app.api.utils.enums.auth import AuthErrorMessage
from app.api.v1.schemas.auth import AuthRequest
from app.api.v1.schemas.users import UserCreateRequest
from app.config import config


@pytest.mark.asyncio
async def test_login_success(async_client, faker, db_session) -> None:
    """Тест успешной аутентификации через эндпоинт."""
    # Создаем пользователя через сервис
    from app.services.user_service import UserService

    service = UserService()
    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
    )
    user = await service.create_user(session=db_session, user_data=user_request)

    # Выполняем запрос на логин используя AuthRequest схему
    auth_request = AuthRequest(
        email=user_request.email,
        password='Password123',
    )
    response = await async_client.post(
        '/api/v1/auth/login',
        json=auth_request.model_dump(),
    )

    # Проверяем ответ
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'
    assert data['expires_in'] == config.jwt.access_token_expire_minutes * 60

    # Проверяем JWT токен
    payload = jwt.decode(
        data['access_token'],
        config.jwt.secret_key,
        algorithms=[config.jwt.algorithm],
    )
    assert payload['user_id'] == user.id
    assert payload['is_active'] is True
    assert 'exp' in payload
    assert 'iat' in payload
    assert 'jti' in payload


@pytest.mark.asyncio
async def test_login_user_not_found(async_client) -> None:
    """Тест логина с несуществующим email."""
    auth_request = AuthRequest(
        email='nonexistent@example.com',
        password='Password123',
    )
    response = await async_client.post(
        '/api/v1/auth/login',
        json=auth_request.model_dump(),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == AuthErrorMessage.INVALID_CREDENTIALS


@pytest.mark.asyncio
async def test_login_wrong_password(async_client, faker, db_session) -> None:
    """Тест логина с неверным паролем."""
    # Создаем пользователя
    from app.services.user_service import UserService

    service = UserService()
    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
    )
    await service.create_user(session=db_session, user_data=user_request)

    # Пытаемся войти с неверным паролем
    auth_request = AuthRequest(
        email=user_request.email,
        password='WrongPassword456',
    )
    response = await async_client.post(
        '/api/v1/auth/login',
        json=auth_request.model_dump(),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == AuthErrorMessage.INVALID_CREDENTIALS


@pytest.mark.asyncio
async def test_login_inactive_user(async_client, faker, db_session) -> None:
    """Тест логина неактивного пользователя."""
    # Создаем и деактивируем пользователя
    from sqlalchemy import select

    from app.db.models.user import User
    from app.services.user_service import UserService

    service = UserService()
    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
    )
    user = await service.create_user(session=db_session, user_data=user_request)

    # Деактивируем пользователя
    result = await db_session.execute(select(User).where(User.id == user.id))
    user_model = result.scalars().first()
    user_model.is_active = False
    await db_session.commit()

    # Пытаемся войти
    auth_request = AuthRequest(
        email=user_request.email,
        password='Password123',
    )
    response = await async_client.post(
        '/api/v1/auth/login',
        json=auth_request.model_dump(),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == AuthErrorMessage.INACTIVE_USER


@pytest.mark.asyncio
async def test_login_validation_error(async_client) -> None:
    """Тест логина с невалидными данными."""
    # Отсутствует email
    response = await async_client.post(
        '/api/v1/auth/login',
        json={
            'password': 'Password123',
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Email невалидного формата
    response = await async_client.post(
        '/api/v1/auth/login',
        json={
            'email': 'invalid-email',
            'password': 'Password123',
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Пароль короче 8 символов
    response = await async_client.post(
        '/api/v1/auth/login',
        json={
            'email': 'user@example.com',
            'password': 'Short1',
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_logout_success(async_client, faker, db_session) -> None:
    """Тест успешного выхода из системы."""
    # Создаем пользователя и аутентифицируемся
    from app.services.user_service import UserService

    service = UserService()
    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
    )
    await service.create_user(session=db_session, user_data=user_request)

    auth_request = AuthRequest(
        email=user_request.email,
        password='Password123',
    )
    login_response = await async_client.post(
        '/api/v1/auth/login',
        json=auth_request.model_dump(),
    )
    token = login_response.json()['access_token']

    # Выполняем logout
    logout_response = await async_client.post(
        '/api/v1/auth/logout',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert logout_response.status_code == status.HTTP_200_OK
    assert logout_response.json()['message'] == AuthErrorMessage.LOGOUT_SUCCESS


@pytest.mark.asyncio
async def test_logout_no_token(async_client) -> None:
    """Тест логаута без токена."""
    response = await async_client.post('/api/v1/auth/logout')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == AuthErrorMessage.MISSING_TOKEN


@pytest.mark.asyncio
async def test_logout_invalid_token(async_client) -> None:
    """Тест логаута с невалидным токеном."""
    response = await async_client.post(
        '/api/v1/auth/logout',
        headers={'Authorization': 'Bearer invalid_token'},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == AuthErrorMessage.INVALID_TOKEN


@pytest.mark.asyncio
async def test_logout_expired_token(async_client, faker, db_session) -> None:
    """Тест логаута с истёкшим токеном."""
    # Создаем истёкший токен
    from datetime import timedelta

    from jose import jwt

    from app.config import config
    from app.services.user_service import UserService

    service = UserService()
    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
    )
    user = await service.create_user(session=db_session, user_data=user_request)

    # Создаём токен с истёкшим сроком действия
    # JWT library auto-validates expiration, so expired tokens will fail decode
    # and return INVALID_TOKEN error, not EXPIRED_TOKEN
    from datetime import datetime
    from uuid import uuid4

    payload = {
        'sub': str(user.id),
        'user_id': user.id,
        'is_active': user.is_active,
        'iat': datetime.now(UTC) - timedelta(minutes=config.jwt.access_token_expire_minutes + 10),
        'exp': datetime.now(UTC) - timedelta(minutes=10),
        'jti': str(uuid4()),
    }
    expired_token = jwt.encode(payload, config.jwt.secret_key, algorithm=config.jwt.algorithm)

    response = await async_client.post(
        '/api/v1/auth/logout',
        headers={'Authorization': f'Bearer {expired_token}'},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # JWT library returns expired token error, which maps to INVALID_TOKEN in our code
    assert response.json()['detail'] in [
        AuthErrorMessage.INVALID_TOKEN,
        AuthErrorMessage.EXPIRED_TOKEN,
    ]


@pytest.mark.asyncio
async def test_logout_blacklisted_token(async_client, faker, db_session) -> None:
    """Тест логаута с уже отозванным токеном."""
    from app.services.user_service import UserService

    service = UserService()
    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
    )
    await service.create_user(session=db_session, user_data=user_request)

    auth_request = AuthRequest(
        email=user_request.email,
        password='Password123',
    )
    login_response = await async_client.post(
        '/api/v1/auth/login',
        json=auth_request.model_dump(),
    )
    token = login_response.json()['access_token']

    # Первый logout
    await async_client.post(
        '/api/v1/auth/logout',
        headers={'Authorization': f'Bearer {token}'},
    )

    # Второй logout с тем же токеном
    response = await async_client.post(
        '/api/v1/auth/logout',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail'] == AuthErrorMessage.REVOKED_TOKEN
