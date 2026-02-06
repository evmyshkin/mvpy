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
    assert data['is_active'] is True

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
    assert data['is_active'] is True
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
            'repeat_password': 'Password123',
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
            'repeat_password': 'Password123',
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
            'repeat_password': 'Password123',
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
            'repeat_password': 'Password123',
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
            'repeat_password': 'Pass1',
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
            'repeat_password': 'password123',
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
            'repeat_password': 'PASSWORD123',
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
            'repeat_password': 'Password',
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
            'repeat_password': 'Password123' * 10,
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
        repeat_password='NewPassword456',
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
    assert data['is_active'] is True
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
        repeat_password='Password123',
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


# Тесты для деактивации пользователя (DELETE /api/v1/users/{user_id})
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
    user_id = create_response.json()['id']

    # Act - деактивируем пользователя
    delete_response = await async_client.delete(f'/api/v1/users/{user_id}')

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
    response = await async_client.delete('/api/v1/users/99999')

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
    user_id = create_response.json()['id']

    # Первая деактивация
    delete_response1 = await async_client.delete(f'/api/v1/users/{user_id}')
    assert delete_response1.status_code == 204

    # Act - вторая попытка деактивации
    delete_response2 = await async_client.delete(f'/api/v1/users/{user_id}')

    # Assert - должен вернуть 404 как для несуществующего пользователя
    assert delete_response2.status_code == 404
    assert delete_response2.json()['detail'] == ErrorMessages.USER_NOT_FOUND.value


# Тесты для получения пользователя по ID (GET /api/v1/users/{user_id})
@pytest.mark.asyncio
async def test_get_user_by_id_success(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест успешного получения пользователя по ID.

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
    created_user = create_response.json()

    # Act - получаем пользователя по ID
    get_response = await async_client.get(f'/api/v1/users/{created_user["id"]}')

    # Assert - проверяем статус и данные ответа
    assert get_response.status_code == 200
    data = get_response.json()
    assert data['id'] == created_user['id']
    assert data['email'] == valid_user_request.email
    assert data['first_name'] == valid_user_request.first_name
    assert data['last_name'] == valid_user_request.last_name
    assert data['is_active'] is True

    # Проверяем что пароль не возвращается
    assert 'password' not in data
    assert 'password_hash' not in data


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(
    async_client: AsyncClient,
) -> None:
    """Тест получения несуществующего пользователя.

    Args:
        async_client: Асинхронный HTTP клиент
    """
    # Act - получаем несуществующего пользователя
    response = await async_client.get('/api/v1/users/99999')

    # Assert - должен вернуть 404 с русским сообщением
    assert response.status_code == 404
    assert response.json()['detail'] == 'Пользователь не найден'


@pytest.mark.asyncio
async def test_get_user_by_id_invalid_format(
    async_client: AsyncClient,
) -> None:
    """Тест получения с невалидным форматом ID.

    Args:
        async_client: Асинхронный HTTP клиент
    """
    # Act - отправляем запрос с невалидным ID (строка вместо числа)
    response = await async_client.get('/api/v1/users/abc')

    # Assert - должен вернуть 422 (ошибка валидации)
    assert response.status_code == 422


# Тесты для получения списка всех пользователей (GET /api/v1/users/)
@pytest.mark.asyncio
async def test_get_all_users_success(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
    faker,
) -> None:
    """Тест успешного получения списка всех пользователей.

    Args:
        async_client: Асинхронный HTTP клиент
        valid_user_request: Валидный запрос на создание пользователя
        faker: Генератор тестовых данных
    """
    # Arrange - создаём нескольких пользователей
    await async_client.post('/api/v1/users/', json=valid_user_request.model_dump())

    user2_request = UserCreateRequest(
        email=faker.email(),
        first_name='Пётр',
        last_name='Петров',
        password='Password123',
        repeat_password='Password123',
    )
    await async_client.post('/api/v1/users/', json=user2_request.model_dump())

    # Act - получаем список всех пользователей
    response = await async_client.get('/api/v1/users/')

    # Assert - проверяем статус и массив с пользователями
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2

    # Проверяем структуру первого пользователя
    assert 'id' in data[0]
    assert 'email' in data[0]
    assert 'first_name' in data[0]
    assert 'last_name' in data[0]
    assert 'is_active' in data[0]
    assert data[0]['is_active'] is True
    # Проверяем что пароль не возвращается
    assert 'password' not in data[0]
    assert 'password_hash' not in data[0]


@pytest.mark.asyncio
async def test_get_all_users_empty_list(
    async_client: AsyncClient,
) -> None:
    """Тест получения пустого списка пользователей.

    Args:
        async_client: Асинхронный HTTP клиент
    """
    # Act - получаем список пользователей (не создавая ни одного)
    response = await async_client.get('/api/v1/users/')

    # Assert - должен вернуть 200 с пустым массивом
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_all_users_password_not_exposed(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест что пароль не возвращается в списке пользователей.

    Args:
        async_client: Асинхронный HTTP клиент
        valid_user_request: Валидный запрос на создание пользователя
    """
    # Arrange - создаём пользователя
    await async_client.post('/api/v1/users/', json=valid_user_request.model_dump())

    # Act - получаем список всех пользователей
    response = await async_client.get('/api/v1/users/')

    # Assert - проверяем что password_hash отсутствует в ответе
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert 'password' not in data[0]
    assert 'password_hash' not in data[0]


@pytest.mark.asyncio
async def test_get_user_by_id_vs_all_users(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
    faker,
) -> None:
    """Тест различия между получением по ID и списком всех пользователей.

    Args:
        async_client: Асинхронный HTTP клиент
        valid_user_request: Валидный запрос на создание пользователя
        faker: Генератор тестовых данных
    """
    # Arrange - создаём нескольких пользователей
    response1 = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    assert response1.status_code == 201
    user1_id = response1.json()['id']

    user2_request = UserCreateRequest(
        email=faker.email(),
        first_name='Пётр',
        last_name='Петров',
        password='Password123',
        repeat_password='Password123',
    )
    response2 = await async_client.post('/api/v1/users/', json=user2_request.model_dump())
    assert response2.status_code == 201

    # Act 1 - получаем по ID (должен вернуть одного пользователя)
    get_response = await async_client.get(f'/api/v1/users/{user1_id}')

    # Act 2 - получаем всех пользователей (должен вернуть список)
    all_response = await async_client.get('/api/v1/users/')

    # Assert - результаты должны различаться
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert isinstance(get_data, dict)
    assert get_data['id'] == user1_id

    assert all_response.status_code == 200
    all_data = all_response.json()
    assert isinstance(all_data, list)
    assert len(all_data) == 2
    # При получении по ID возвращается dict, при получении всех - list
    assert isinstance(get_data, dict)
    assert isinstance(all_data, list)


@pytest.mark.asyncio
async def test_get_all_users_excludes_deactivated(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
    faker,
) -> None:
    """Тест того, что деактивированные пользователи исключаются из списка.

    Args:
        async_client: Асинхронный HTTP клиент
        valid_user_request: Валидный запрос на создание пользователя
        faker: Генератор тестовых данных
    """
    # Arrange - создаём двух пользователей
    response1 = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    assert response1.status_code == 201
    user1_id = response1.json()['id']

    user2_request = UserCreateRequest(
        email=faker.email(),
        first_name='Пётр',
        last_name='Петров',
        password='Password123',
        repeat_password='Password123',
    )
    response2 = await async_client.post('/api/v1/users/', json=user2_request.model_dump())
    assert response2.status_code == 201
    user2_email = response2.json()['email']

    # Деактивируем первого пользователя
    delete_response = await async_client.delete(f'/api/v1/users/{user1_id}')
    assert delete_response.status_code == 204

    # Act - получаем список всех пользователей
    all_response = await async_client.get('/api/v1/users/')

    # Assert - должен вернуться только второй пользователь
    assert all_response.status_code == 200
    data = all_response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['email'] == user2_email
    assert data[0]['is_active'] is True


# Тесты для проверки совпадения паролей
@pytest.mark.asyncio
async def test_create_user_passwords_do_not_match(
    async_client: AsyncClient,
    faker,
) -> None:
    """Тест несовпадения паролей при создании пользователя (422)."""
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password': 'Password123',
            'repeat_password': 'DifferentPassword123',
        },
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('repeat_password' in str(err) or 'Пароли не совпадают' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_create_user_missing_repeat_password(
    async_client: AsyncClient,
    faker,
) -> None:
    """Тест отсутствия repeat_password при создании пользователя (422)."""
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password': 'Password123',
        },
    )

    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('repeat_password' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_update_user_passwords_do_not_match(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест несовпадения паролей при обновлении пользователя (422)."""
    # Arrange - создаём пользователя
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    user_id = create_response.json()['id']

    # Act - пытаемся обновить с несовпадающими паролями
    response = await async_client.put(
        f'/api/v1/users/{user_id}',
        json={
            'password': 'NewPassword456',
            'repeat_password': 'DifferentPassword456',
        },
    )

    # Assert - должна быть ошибка валидации
    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('repeat_password' in str(err) or 'Пароли не совпадают' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_update_user_password_without_repeat(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест указания password без repeat_password при обновлении (422)."""
    # Arrange - создаём пользователя
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    user_id = create_response.json()['id']

    # Act - указываем только password без repeat_password
    response = await async_client.put(
        f'/api/v1/users/{user_id}',
        json={'password': 'NewPassword456'},
    )

    # Assert - должна быть ошибка валидации
    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('repeat_password' in str(err) or 'Необходимо подтвердить пароль' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_update_user_repeat_password_without_password(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест указания repeat_password без password при обновлении (422)."""
    # Arrange - создаём пользователя
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    user_id = create_response.json()['id']

    # Act - указываем только repeat_password без password
    response = await async_client.put(
        f'/api/v1/users/{user_id}',
        json={'repeat_password': 'NewPassword456'},
    )

    # Assert - должна быть ошибка валидации
    assert response.status_code == 422
    errors = response.json()['detail']
    assert any('password' in str(err) or 'Необходимо указать пароль' in str(err) for err in errors)


@pytest.mark.asyncio
async def test_update_user_with_matching_passwords(
    async_client: AsyncClient,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест успешного обновления пароля при совпадающих паролях (200)."""
    # Arrange - создаём пользователя
    create_response = await async_client.post(
        '/api/v1/users/',
        json=valid_user_request.model_dump(),
    )
    user_id = create_response.json()['id']

    # Act - обновляем с совпадающими паролями
    response = await async_client.put(
        f'/api/v1/users/{user_id}',
        json={
            'password': 'NewPassword456',
            'repeat_password': 'NewPassword456',
        },
    )

    # Assert - обновление должно пройти успешно
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == user_id
    assert 'password' not in data
    assert 'password_hash' not in data
