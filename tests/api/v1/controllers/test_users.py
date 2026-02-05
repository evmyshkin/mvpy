"""Тесты для создания пользователей."""

import pytest
from httpx import AsyncClient

from app.api.v1.schemas.users import UserCreateRequest


@pytest.mark.asyncio
async def test_create_user_success(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест успешного создания пользователя.

    Args:
        async_client: Асинхронный HTTP клиент
        valid_user_request: Валидный запрос на создание пользователя
    """
    response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )

    assert response.status_code == 201
    data = response.json()

    # Проверяем структуру и значения
    assert 'id' in data
    assert isinstance(data['id'], int)

    assert data['email'] == valid_user_request.email
    assert data['first_name'] == valid_user_request.first_name
    assert data['last_name'] == valid_user_request.last_name

    # Проверяем что пароль не возвращается
    assert 'password' not in data
    assert 'password_hash' not in data


@pytest.mark.asyncio
async def test_create_user_duplicate_email(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест дубликата email.

    Args:
        async_client: Асинхронный HTTP клиент
        valid_user_request: Валидный запрос на создание пользователя
    """
    # Первый запрос
    response1 = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )

    assert response1.status_code == 201
    data1 = response1.json()
    user_id = data1['id']
    assert user_id > 0

    # Второй запрос с тем же email
    response2 = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )

    assert response2.status_code == 409
    detail = response2.json()['detail']
    assert detail == 'Пользователь с таким email уже существует'


@pytest.mark.asyncio
async def test_create_user_password_not_exposed(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест что пароль не возвращается в API ответе.

    Args:
        async_client: Асинхронный HTTP клиент
        valid_user_request: Валидный запрос на создание пользователя
    """
    # Создаем пользователя через API
    response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )

    assert response.status_code == 201
    data = response.json()

    # Проверяем что пароль не возвращается в ответе (безопасность)
    assert 'password' not in data
    assert 'password_hash' not in data

    # Проверяем что пользователь создан с корректными данными
    assert data['email'] == valid_user_request.email
    assert data['first_name'] == valid_user_request.first_name
    assert data['last_name'] == valid_user_request.last_name
    assert 'id' in data


# Тесты валидации имени/фамилии (T026)
@pytest.mark.asyncio
async def test_create_user_first_name_with_digits_fails(
    async_client: AsyncClient,
    faker,
) -> None:
    """Тест что имя с цифрами возвращает 422.

    Args:
        async_client: Асинхронный HTTP клиент
        faker: Генератор тестовых данных
    """
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'Иван1',
            'last_name': 'Иванов',
            'password': 'Password123',
        },
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('first_name' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_create_user_last_name_with_special_chars_fails(
    async_client: AsyncClient,
    faker,
) -> None:
    """Тест что фамилия со спецсимволами возвращает 422.

    Args:
        async_client: Асинхронный HTTP клиент
        faker: Генератор тестовых данных
    """
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'Иван',
            'last_name': 'Иванов_Петров',
            'password': 'Password123',
        },
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('last_name' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_create_user_first_name_too_long_fails(
    async_client: AsyncClient,
    faker,
) -> None:
    """Тест что имя длиннее 100 символов возвращает 422.

    Args:
        async_client: Асинхронный HTTP клиент
        faker: Генератор тестовых данных
    """
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'А' * 101,
            'last_name': 'Иванов',
            'password': 'Password123',
        },
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('first_name' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_create_user_name_with_hyphen_succeeds(
    async_client: AsyncClient,
    faker,
) -> None:
    """Тест что имя с тире проходит валидацию.

    Args:
        async_client: Асинхронный HTTP клиент
        faker: Генератор тестовых данных
    """
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'Мария-Изабелла',
            'last_name': 'Салтыков-Щедрин',
            'password': 'Password123',
        },
    )

    assert response.status_code == 201


# Тесты валидации пароля (T027)
@pytest.mark.asyncio
async def test_create_user_password_too_short_fails(
    async_client: AsyncClient,
    faker,
) -> None:
    """Тест что пароль короче 8 символов возвращает 422.

    Args:
        async_client: Асинхронный HTTP клиент
        faker: Генератор тестовых данных
    """
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password': 'Pass1',
        },
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('password' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_create_user_password_no_uppercase_fails(
    async_client: AsyncClient,
    faker,
) -> None:
    """Тест что пароль без заглавной буквы возвращает 422.

    Args:
        async_client: Асинхронный HTTP клиент
        faker: Генератор тестовых данных
    """
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password': 'password123',
        },
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('password' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_create_user_password_no_lowercase_fails(
    async_client: AsyncClient,
    faker,
) -> None:
    """Тест что пароль без строчной буквы возвращает 422.

    Args:
        async_client: Асинхронный HTTP клиент
        faker: Генератор тестовых данных
    """
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password': 'PASSWORD123',
        },
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('password' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_create_user_password_no_digit_fails(
    async_client: AsyncClient,
    faker,
) -> None:
    """Тест что пароль без цифры возвращает 422.

    Args:
        async_client: Асинхронный HTTP клиент
        faker: Генератор тестовых данных
    """
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password': 'Password',
        },
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('password' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_create_user_password_too_long_fails(
    async_client: AsyncClient,
    faker,
) -> None:
    """Тест что пароль длиннее 100 символов возвращает 422.

    Args:
        async_client: Асинхронный HTTP клиент
        faker: Генератор тестовых данных
    """
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password': 'Password123' * 10,
        },
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('password' in str(err) for err in errors)
