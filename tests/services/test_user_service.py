"""Тесты для UserService."""

import pytest

from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.status import HTTP_404_NOT_FOUND
from starlette.status import HTTP_409_CONFLICT

from app.api.v1.schemas.users import UserCreateRequest
from app.api.v1.schemas.users import UserCreateResponse
from app.api.v1.schemas.users import UserUpdateRequest
from app.services.error_messages import ErrorMessages
from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_create_user_duplicate_email(
    db_session,
    user_service: UserService,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест создания пользователя с дубликатом email."""
    # Создаём первого пользователя
    created_user = await user_service.create_user(session=db_session, user_data=valid_user_request)

    # Проверяем что is_active=True при создании
    assert created_user.is_active is True

    # Пытаемся создать второго с тем же email
    duplicate_request = UserCreateRequest(
        email=valid_user_request.email,  # Тот же email
        first_name='Пётр',
        last_name='Петров',
        password='Password456',
        repeat_password='Password456',
    )

    with pytest.raises(HTTPException) as exc_info:
        await user_service.create_user(session=db_session, user_data=duplicate_request)

    assert exc_info.value.status_code == HTTP_409_CONFLICT
    assert exc_info.value.detail == ErrorMessages.USER_EMAIL_EXISTS.value


@pytest.mark.asyncio
async def test_update_user_success(
    db_session,
    user_service: UserService,
    existing_user: UserCreateResponse,
) -> None:
    """Тест успешного обновления всех полей пользователя."""
    update_request = UserUpdateRequest(
        email='newemail@example.com',
        first_name='Пётр',
        last_name='Петров',
        password='NewPassword456',
        repeat_password='NewPassword456',
    )

    updated_user = await user_service.update_user(
        session=db_session,
        user_id=existing_user.id,
        user_data=update_request,
    )

    assert updated_user.id == existing_user.id
    assert updated_user.email == 'newemail@example.com'
    assert updated_user.first_name == 'Пётр'
    assert updated_user.last_name == 'Петров'
    assert updated_user.is_active is True


@pytest.mark.asyncio
async def test_update_user_partial(
    db_session,
    user_service: UserService,
    existing_user: UserCreateResponse,
) -> None:
    """Тест частичного обновления одного поля."""
    update_request = UserUpdateRequest(first_name='Пётр')

    updated_user = await user_service.update_user(
        session=db_session,
        user_id=existing_user.id,
        user_data=update_request,
    )

    assert updated_user.id == existing_user.id
    assert updated_user.first_name == 'Пётр'
    # Другие поля не должны измениться
    assert updated_user.last_name == existing_user.last_name
    assert updated_user.email == existing_user.email
    assert updated_user.is_active is True


@pytest.mark.asyncio
async def test_update_user_not_found(
    db_session,
    user_service: UserService,
) -> None:
    """Тест обновления несуществующего пользователя."""
    update_request = UserUpdateRequest(first_name='Пётр')

    with pytest.raises(HTTPException) as exc_info:
        await user_service.update_user(
            session=db_session,
            user_id=99999,
            user_data=update_request,
        )

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == ErrorMessages.USER_NOT_FOUND.value


@pytest.mark.asyncio
async def test_update_user_duplicate_email(
    db_session,
    user_service: UserService,
    existing_user: UserCreateResponse,
) -> None:
    """Тест обновления с дубликатом email от другого пользователя."""
    # Создаём второго пользователя
    second_user_request = UserCreateRequest(
        email='second@example.com',
        first_name='Сергей',
        last_name='Сергеев',
        password='Password789',
        repeat_password='Password789',
    )
    second_user = await user_service.create_user(session=db_session, user_data=second_user_request)

    # Пытаемся обновить первого пользователя с email второго
    update_request = UserUpdateRequest(email=second_user.email)

    with pytest.raises(HTTPException) as exc_info:
        await user_service.update_user(
            session=db_session,
            user_id=existing_user.id,
            user_data=update_request,
        )

    assert exc_info.value.status_code == HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == ErrorMessages.USER_EMAIL_EXISTS.value


@pytest.mark.asyncio
async def test_update_user_same_email(
    db_session,
    user_service: UserService,
    existing_user: UserCreateResponse,
) -> None:
    """Тест обновления с тем же email (не должно вызывать ошибку)."""
    update_request = UserUpdateRequest(
        email=existing_user.email,  # Тот же email
        first_name='Пётр',
    )

    updated_user = await user_service.update_user(
        session=db_session,
        user_id=existing_user.id,
        user_data=update_request,
    )

    assert updated_user.id == existing_user.id
    assert updated_user.email == existing_user.email
    assert updated_user.first_name == 'Пётр'
    assert updated_user.is_active is True


@pytest.mark.asyncio
async def test_update_user_password_hashed(
    db_session,
    user_service: UserService,
    existing_user: UserCreateResponse,
) -> None:
    """Тест того, что пароль захеширован при обновлении."""
    new_password = 'NewPassword456'
    update_request = UserUpdateRequest(password=new_password, repeat_password=new_password)

    await user_service.update_user(
        session=db_session,
        user_id=existing_user.id,
        user_data=update_request,
    )

    # Проверяем, что пароль не хранится в открытом виде
    from app.db.crud.users import UsersCrud

    user_from_db = await UsersCrud().find_one_or_none(db_session, id=existing_user.id)

    assert user_from_db is not None
    assert user_from_db.password_hash != new_password
    # Проверяем, что пароль захеширован (bcrypt хеши начинаются с $2b$)
    assert user_from_db.password_hash.startswith('$2b$')


# Тесты для деактивации пользователя
@pytest.mark.asyncio
async def test_deactivate_user_success(
    db_session,
    user_service: UserService,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест успешной деактивации пользователя.

    Args:
        db_session: Сессия базы данных
        user_service: Сервис пользователей
        valid_user_request: Валидный запрос на создание пользователя
    """
    # Arrange - создаём пользователя
    created_user = await user_service.create_user(
        session=db_session,
        user_data=valid_user_request,
    )

    # Act - деактивируем пользователя
    await user_service.deactivate_user(
        session=db_session,
        user_id=created_user.id,
    )

    # Assert - проверяем что пользователь деактивирован
    from app.db.crud.users import UsersCrud

    user_from_db = await UsersCrud().find_one_or_none(db_session, id=created_user.id)
    assert user_from_db is not None
    assert user_from_db.is_active is False


@pytest.mark.asyncio
async def test_deactivate_user_not_found(
    db_session,
    user_service: UserService,
) -> None:
    """Тест деактивации несуществующего пользователя.

    Args:
        db_session: Сессия базы данных
        user_service: Сервис пользователей
    """
    # Act & Assert - пытаемся деактивировать несуществующего пользователя
    with pytest.raises(HTTPException) as exc_info:
        await user_service.deactivate_user(
            session=db_session,
            user_id=99999,
        )

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == ErrorMessages.USER_NOT_FOUND.value


@pytest.mark.asyncio
async def test_deactivate_user_already_deactivated(
    db_session,
    user_service: UserService,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест попытки деактивировать уже деактивированного пользователя.

    Args:
        db_session: Сессия базы данных
        user_service: Сервис пользователей
        valid_user_request: Валидный запрос на создание пользователя
    """
    # Arrange - создаём и деактивируем пользователя
    created_user = await user_service.create_user(
        session=db_session,
        user_data=valid_user_request,
    )

    await user_service.deactivate_user(
        session=db_session,
        user_id=created_user.id,
    )

    # Act & Assert - вторая попытка деактивации должна вернуть 404
    with pytest.raises(HTTPException) as exc_info:
        await user_service.deactivate_user(
            session=db_session,
            user_id=created_user.id,
        )

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == ErrorMessages.USER_NOT_FOUND.value


# Тесты для получения пользователя по ID
@pytest.mark.asyncio
async def test_get_user_by_id_success(
    db_session,
    user_service: UserService,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест успешного получения пользователя по ID.

    Args:
        db_session: Сессия базы данных
        user_service: Сервис пользователей
        valid_user_request: Валидный запрос на создание пользователя
    """
    # Arrange - создаём пользователя
    created_user = await user_service.create_user(
        session=db_session,
        user_data=valid_user_request,
    )

    # Act - получаем пользователя по ID
    found_user = await user_service.get_user_by_id(
        session=db_session,
        user_id=created_user.id,
    )

    # Assert - проверяем что пользователь найден
    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.email == created_user.email
    assert found_user.first_name == created_user.first_name
    assert found_user.last_name == created_user.last_name
    assert found_user.is_active is True


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(
    db_session,
    user_service: UserService,
) -> None:
    """Тест получения несуществующего пользователя.

    Args:
        db_session: Сессия базы данных
        user_service: Сервис пользователей
    """
    # Act & Assert - пытаемся получить несуществующего пользователя
    with pytest.raises(HTTPException) as exc_info:
        await user_service.get_user_by_id(
            session=db_session,
            user_id=99999,
        )

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == ErrorMessages.USER_NOT_FOUND.value


# Тесты для поиска пользователя по email
@pytest.mark.asyncio
async def test_search_user_by_email_success(
    db_session,
    user_service: UserService,
    valid_user_request: UserCreateRequest,
) -> None:
    """Тест успешного поиска пользователя по email.

    Args:
        db_session: Сессия базы данных
        user_service: Сервис пользователей
        valid_user_request: Валидный запрос на создание пользователя
    """
    # Arrange - создаём пользователя
    created_user = await user_service.create_user(
        session=db_session,
        user_data=valid_user_request,
    )

    # Act - ищем пользователя по email
    found_user = await user_service.search_user_by_email(
        session=db_session,
        email=created_user.email,
    )

    # Assert - проверяем что пользователь найден с корректными данными
    assert found_user.id == created_user.id
    assert found_user.email == created_user.email
    assert found_user.first_name == created_user.first_name
    assert found_user.last_name == created_user.last_name
    assert found_user.is_active is True


@pytest.mark.asyncio
async def test_search_user_by_email_not_found(
    db_session,
    user_service: UserService,
) -> None:
    """Тест поиска несуществующего пользователя.

    Args:
        db_session: Сессия базы данных
        user_service: Сервис пользователей
    """
    # Act & Assert - пытаемся найти несуществующего пользователя
    with pytest.raises(HTTPException) as exc_info:
        await user_service.search_user_by_email(
            session=db_session,
            email='notfound@example.com',
        )

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert exc_info.value.detail == 'Пользователь с указанным email не найден'


# Тесты для получения списка всех пользователей
@pytest.mark.asyncio
async def test_get_all_users_success(
    db_session,
    user_service: UserService,
    valid_user_request: UserCreateRequest,
    faker,
) -> None:
    """Тест успешного получения списка всех пользователей.

    Args:
        db_session: Сессия базы данных
        user_service: Сервис пользователей
        valid_user_request: Валидный запрос на создание пользователя
        faker: Генератор тестовых данных
    """
    # Arrange - создаём нескольких пользователей
    user1 = await user_service.create_user(
        session=db_session,
        user_data=valid_user_request,
    )

    user2_request = UserCreateRequest(
        email=faker.email(),
        first_name='Пётр',
        last_name='Петров',
        password='Password123',
        repeat_password='Password123',
    )
    user2 = await user_service.create_user(session=db_session, user_data=user2_request)

    # Act - получаем список всех пользователей
    all_users = await user_service.get_all_users(session=db_session)

    # Assert - проверяем что вернулся список с корректным количеством
    assert len(all_users) == 2
    assert all_users[0].id == user1.id
    assert all_users[0].email == user1.email
    assert all_users[0].is_active is True
    assert all_users[1].id == user2.id
    assert all_users[1].email == user2.email
    assert all_users[1].is_active is True


@pytest.mark.asyncio
async def test_get_all_users_empty(
    db_session,
    user_service: UserService,
) -> None:
    """Тест получения пустого списка пользователей.

    Args:
        db_session: Сессия базы данных
        user_service: Сервис пользователей
    """
    # Act - получаем список пользователей (не создавая ни одного)
    all_users = await user_service.get_all_users(session=db_session)

    # Assert - должен вернуться пустой список
    assert len(all_users) == 0
    assert all_users == []


@pytest.mark.asyncio
async def test_get_all_users_excludes_deactivated(
    db_session,
    user_service: UserService,
    valid_user_request: UserCreateRequest,
    faker,
) -> None:
    """Тест того, что деактивированные пользователи исключаются из списка.

    Args:
        db_session: Сессия базы данных
        user_service: Сервис пользователей
        valid_user_request: Валидный запрос на создание пользователя
        faker: Генератор тестовых данных
    """
    # Arrange - создаём двух пользователей
    user1 = await user_service.create_user(
        session=db_session,
        user_data=valid_user_request,
    )

    user2_request = UserCreateRequest(
        email=faker.email(),
        first_name='Пётр',
        last_name='Петров',
        password='Password123',
        repeat_password='Password123',
    )
    user2 = await user_service.create_user(session=db_session, user_data=user2_request)

    # Деактивируем первого пользователя
    await user_service.deactivate_user(session=db_session, user_id=user1.id)

    # Act - получаем список всех пользователей
    all_users = await user_service.get_all_users(session=db_session)

    # Assert - должен вернуться только второй пользователь
    assert len(all_users) == 1
    assert all_users[0].id == user2.id
    assert all_users[0].email == user2.email
    assert all_users[0].is_active is True


# Тесты для автоматического присвоения роли (User Story 3)
@pytest.mark.asyncio
async def test_create_user_without_role_id_assigns_default(
    db_session,
    user_service: UserService,
    faker,
) -> None:
    """Тест UserService create_user с role_id=None присваивает роль user.

    Args:
        db_session: Сессия базы данных
        user_service: Сервис пользователей
        faker: Генератор тестовых данных
    """
    # Arrange - создаём запрос без role_id
    from app.api.v1.schemas.users import UserCreateRequest

    user_request = UserCreateRequest(
        email=faker.email(),
        first_name='Иван',
        last_name='Иванов',
        password='Password123',
        repeat_password='Password123',
        # role_id не указан
    )

    # Act - создаём пользователя
    created_user = await user_service.create_user(
        session=db_session,
        user_data=user_request,
    )

    # Assert - проверяем что пользователю присвоена роль "user" (id=1)
    assert created_user is not None
    assert hasattr(created_user, 'role')
    assert created_user.role.id == 1
    assert created_user.role.name == 'user'
