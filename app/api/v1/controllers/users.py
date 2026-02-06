"""Контроллер для работы с пользователями."""

from fastapi import APIRouter
from fastapi import Depends
from pydantic import EmailStr
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


@router.delete('/{email}')
async def deactivate_user(
    email: str,
    db: AsyncSession = Depends(connector.get_session),
) -> Response:
    """Деактивировать пользователя по email.

    Args:
        email: Email пользователя для деактивации
        db: Асинхронная сессия БД

    Returns:
        204 No Content при успешной деактивации

    Raises:
        HTTPException: Если пользователь не найден или уже деактивирован (404)
    """
    await user_service.deactivate_user(session=db, email=email)
    return Response(status_code=HTTP_204_NO_CONTENT)


@router.get('/', status_code=200)
async def search_users(
    email: EmailStr | None = None,
    db: AsyncSession = Depends(connector.get_session),
) -> UserUpdateResponse | list[UserUpdateResponse]:
    """Поиск пользователей.

    Если указан email - возвращает одного пользователя.
    Если email не указан - возвращает список всех пользователей.

    Args:
        email: Опциональный email пользователя для поиска
        db: Асинхронная сессия БД

    Returns:
        Данные найденного пользователя или список всех пользователей

    Raises:
        HTTPException: Если пользователь не найден при поиске по email (404)
    """
    if email is not None:
        return await user_service.search_user_by_email(session=db, email=email)

    return await user_service.get_all_users(session=db)
