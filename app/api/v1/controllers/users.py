"""Контроллер для работы с пользователями."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter

from app.api.v1.schemas.users import UserCreateRequest, UserCreateResponse
from app.db.session import connector
from app.services.user_service import UserService

router = APIRouter()
user_service = UserService()


@router.post('/', response_model=UserCreateResponse, status_code=201)
async def create_user(
    user_data: UserCreateRequest,
    db: AsyncSession = Depends(connector.get_session),
) -> UserCreateResponse:
    """Создать нового пользователя.

    Args:
        user_data: Данные для создания пользователя
        db: Асинхронная сессия БД

    Returns:
        Данные созданного пользователя
    """
    return await user_service.create_user(
        session=db,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        password=user_data.password,
    )