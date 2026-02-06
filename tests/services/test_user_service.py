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
    await user_service.create_user(session=db_session, user_data=valid_user_request)

    # Пытаемся создать второго с тем же email
    duplicate_request = UserCreateRequest(
        email=valid_user_request.email,  # Тот же email
        first_name='Пётр',
        last_name='Петров',
        password='Password456',
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


@pytest.mark.asyncio
async def test_update_user_password_hashed(
    db_session,
    user_service: UserService,
    existing_user: UserCreateResponse,
) -> None:
    """Тест того, что пароль захеширован при обновлении."""
    new_password = 'NewPassword456'
    update_request = UserUpdateRequest(password=new_password)

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
