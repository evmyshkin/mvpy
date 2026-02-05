"""Тесты для UserService."""

import pytest

from fastapi import HTTPException
from starlette.status import HTTP_409_CONFLICT

from app.api.v1.schemas.users import UserCreateRequest
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
    await user_service.create_user(
        session=db_session,
        email=valid_user_request.email,
        first_name=valid_user_request.first_name,
        last_name=valid_user_request.last_name,
        password=valid_user_request.password,
    )

    # Пытаемся создать второго с тем же email
    with pytest.raises(HTTPException) as exc_info:
        await user_service.create_user(
            session=db_session,
            email=valid_user_request.email,  # Тот же email
            first_name='Пётр',
            last_name='Петров',
            password='Password456',
        )

    assert exc_info.value.status_code == HTTP_409_CONFLICT
    assert exc_info.value.detail == ErrorMessages.USER_EMAIL_EXISTS.value