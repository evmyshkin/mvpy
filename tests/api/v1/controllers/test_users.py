"""Тесты для создания и обновления пользователей."""

import pytest

from httpx import AsyncClient

from app.api.v1.schemas.users import UserCreateRequest
from app.api.v1.schemas.users import UserUpdateRequest
from app.services.error_messages import ErrorMessages


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
    assert detail == ErrorMessages.USER_EMAIL_EXISTS.value


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


# Тесты для обновления пользователя (PUT /api/v1/users/{id})
@pytest.mark.asyncio
async def test_update_user_success(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
    faker,
) -> None:
    """Успешное обновление всех полей пользователя (200)."""
    # Arrange - создаём пользователя
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    assert create_response.status_code == 201
    user_id = create_response.json()['id']

    # Act - обновляем пользователя через Pydantic схему
    update_request = UserUpdateRequest(
        email=faker.email(),
        first_name='Пётр',
        last_name='Петров',
        password='NewPassword456',
    )
    update_response = await async_client.put(
        f'/api/v1/users/{user_id}',
        json=update_request.model_dump(),
    )

    # Assert
    assert update_response.status_code == 200
    data = update_response.json()
    assert data['id'] == user_id
    assert data['first_name'] == 'Пётр'
    assert data['last_name'] == 'Петров'
    assert 'password' not in data
    assert 'password_hash' not in data


@pytest.mark.asyncio
async def test_update_user_partial(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Частичное обновление одного поля (200)."""
    # Arrange
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    user_id = create_response.json()['id']
    original_email = create_response.json()['email']

    # Act - обновляем только first_name через Pydantic
    update_request = UserUpdateRequest(first_name='Пётр')
    update_response = await async_client.put(
        f'/api/v1/users/{user_id}',
        json=update_request.model_dump(),
    )

    # Assert
    assert update_response.status_code == 200
    data = update_response.json()
    assert data['id'] == user_id
    assert data['first_name'] == 'Пётр'
    assert data['email'] == original_email  # Без изменений


@pytest.mark.asyncio
async def test_update_user_not_found(
    async_client: AsyncClient,
) -> None:
    """Несуществующий user_id (404)."""
    update_request = UserUpdateRequest(first_name='Пётр')
    response = await async_client.put(
        '/api/v1/users/99999',
        json=update_request.model_dump(),
    )

    assert response.status_code == 404
    assert response.json()['detail'] == ErrorMessages.USER_NOT_FOUND.value


@pytest.mark.asyncio
async def test_update_user_duplicate_email(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
    faker,
) -> None:
    """Duplicate email (400)."""
    # Arrange - создаём двух пользователей
    response1 = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    user1_id = response1.json()['id']

    user2_request = UserCreateRequest(
        email=faker.email(),
        first_name='Мария',
        last_name='Сидорова',
        password='Password123',
    )
    response2 = await async_client.post(
        '/api/v1/users/',
        json=user2_request.model_dump(),
    )
    user2_email = response2.json()['email']

    # Act - пытаемся обновить user1 с email пользователя user2 через Pydantic
    update_request = UserUpdateRequest(email=user2_email)
    update_response = await async_client.put(
        f'/api/v1/users/{user1_id}',
        json=update_request.model_dump(),
    )

    # Assert
    assert update_response.status_code == 400
    assert update_response.json()['detail'] == ErrorMessages.USER_EMAIL_EXISTS.value


@pytest.mark.asyncio
async def test_update_user_invalid_email(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Невалидный формат email (422)."""
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    user_id = create_response.json()['id']

    # Pydantic не позволит создать невалидный UserUpdateRequest,
    # поэтому тестируем на уровне HTTP с невалидным JSON
    response = await async_client.put(
        f'/api/v1/users/{user_id}',
        json={'email': 'invalid-email'},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_user_invalid_name(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Имя с цифрами (422)."""
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    user_id = create_response.json()['id']

    # Тестируем на уровне HTTP с невалидными данными
    response = await async_client.put(
        f'/api/v1/users/{user_id}',
        json={'first_name': 'Иван1'},
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('first_name' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_update_user_weak_password(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Слабый пароль (422)."""
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    user_id = create_response.json()['id']

    response = await async_client.put(
        f'/api/v1/users/{user_id}',
        json={'password': 'weak'},
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('password' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_update_user_all_errors(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Множественные ошибки валидации (422)."""
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    user_id = create_response.json()['id']

    response = await async_client.put(
        f'/api/v1/users/{user_id}',
        json={
            'email': 'invalid',
            'first_name': 'Иван1',
            'last_name': 'Петров_Сидоров',
            'password': 'weak',
        },
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    # Проверяем наличие множественных ошибок
    error_fields = {
        err['loc'][0] for err in errors if isinstance(err.get('loc'), list) and err['loc']
    }
    assert 'email' in error_fields or any('email' in str(err).lower() for err in errors)
    assert 'first_name' in error_fields or any('first_name' in str(err).lower() for err in errors)
    assert 'password' in error_fields or any('password' in str(err).lower() for err in errors)


# Тесты для деактивации пользователя (DELETE /api/v1/users/{email})
@pytest.mark.asyncio
async def test_deactivate_user_success(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест успешной деактивации пользователя.

    Args:
        async_client: Асинхронный HTTP клиент
        valid_user_request: Валидный запрос на создание пользователя
    """
    # Arrange - создаём пользователя
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    assert create_response.status_code == 201
    user_email = create_response.json()['email']

    # Act - деактивируем пользователя
    delete_response = await async_client.delete(f'/api/v1/users/{user_email}')

    # Assert - проверяем статус 204 No Content
    assert delete_response.status_code == 204
    assert delete_response.content == b''


@pytest.mark.asyncio
async def test_deactivate_user_not_found(
    async_client: AsyncClient,
) -> None:
    """Тест попытки деактивировать несуществующего пользователя.

    Args:
        async_client: Асинхронный HTTP клиент
    """
    # Act - пытаемся деактивировать несуществующего пользователя
    response = await async_client.delete('/api/v1/users/nonexistent@example.com')

    # Assert - должен вернуть 404
    assert response.status_code == 404
    assert response.json()['detail'] == ErrorMessages.USER_NOT_FOUND.value


@pytest.mark.asyncio
async def test_deactivate_user_already_deactivated(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест попытки деактивировать уже деактивированного пользователя.

    Args:
        async_client: Асинхронный HTTP клиент
        valid_user_request: Валидный запрос на создание пользователя
    """
    # Arrange - создаём и деактивируем пользователя
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    assert create_response.status_code == 201
    user_email = create_response.json()['email']

    # Первая деактивация
    delete_response1 = await async_client.delete(f'/api/v1/users/{user_email}')
    assert delete_response1.status_code == 204

    # Act - вторая попытка деактивации
    delete_response2 = await async_client.delete(f'/api/v1/users/{user_email}')

    # Assert - должен вернуть 404 как для несуществующего пользователя
    assert delete_response2.status_code == 404
    assert delete_response2.json()['detail'] == ErrorMessages.USER_NOT_FOUND.value
