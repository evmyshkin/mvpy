"""Контроллер для работы с ролями."""

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.api.v1.schemas.roles import RoleResponse
from app.db.models.user import User
from app.db.session import connector
from app.services.role_service import RoleService

router = APIRouter()
role_service = RoleService()


@router.get('/', response_model=list[RoleResponse], status_code=200, tags=['roles'])
async def get_roles(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(connector.get_session),
) -> list[RoleResponse]:
    """Получить список всех ролей.

    Args:
        current_user: Текущий аутентифицированный пользователь
        db: Асинхронная сессия БД

    Returns:
        Список всех ролей в системе
    """
    return await role_service.get_roles(session=db)


@router.get('/{role_id}', response_model=RoleResponse, status_code=200, tags=['roles'])
async def get_role_by_id(
    role_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(connector.get_session),
) -> RoleResponse:
    """Получить роль по ID.

    Args:
        role_id: ID роли
        db: Асинхронная сессия БД
        current_user: Текущий аутентифицированный пользователь

    Returns:
        Данные роли

    Raises:
        HTTPException: Если роль не найдена (404)
    """
    return await role_service.get_role_by_id(session=db, role_id=role_id)
