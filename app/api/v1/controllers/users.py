"""Контроллер для работы с пользователями."""

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response
from starlette.status import HTTP_204_NO_CONTENT

from app.api.v1.schemas.users import UserCreateRequest
from app.api.v1.schemas.users import UserCreateResponse
from app.api.v1.schemas.users import UserUpdateRequest
from app.api.v1.schemas.users import UserUpdateResponse
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
    return await user_service.create_user(session=db, user_data=user_data)


@router.put('/{user_id}', response_model=UserUpdateResponse, status_code=200)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: AsyncSession = Depends(connector.get_session),
) -> UserUpdateResponse:
    """Обновить данные пользователя.

    Args:
        user_id: ID пользователя для обновления
        user_data: Данные для обновления пользователя
        db: Асинхронная сессия БД

    Returns:
        Данные обновлённого пользователя
    """
    return await user_service.update_user(session=db, user_id=user_id, user_data=user_data)


@router.delete('/{user_id}')
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(connector.get_session),
) -> Response:
    """Деактивировать пользователя по ID.

    Args:
        user_id: ID пользователя для деактивации
        db: Асинхронная сессия БД

    Returns:
        204 No Content при успешной деактивации

    Raises:
        HTTPException: Если пользователь не найден (404)
    """
    await user_service.deactivate_user(session=db, user_id=user_id)
    return Response(status_code=HTTP_204_NO_CONTENT)


@router.get('/{user_id}', status_code=200)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(connector.get_session),
) -> UserUpdateResponse:
    """Получить пользователя по ID.

    Args:
        user_id: ID пользователя
        db: Асинхронная сессия БД

    Returns:
        Данные найденного пользователя, даже неактивного.

    Raises:
        HTTPException: Если пользователь не найден (404)
    """
    return await user_service.get_user_by_id(session=db, user_id=user_id)


@router.get('/', status_code=200)
async def get_all_users(
    db: AsyncSession = Depends(connector.get_session),
) -> list[UserUpdateResponse]:
    """Получить список всех активных пользователей.

    Args:
        db: Асинхронная сессия БД

    Returns:
        Список всех активных пользователей
    """
    return await user_service.get_all_users(session=db)
