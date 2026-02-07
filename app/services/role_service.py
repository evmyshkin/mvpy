"""Сервис для работы с ролями."""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND

from app.api.v1.schemas.roles import RoleResponse
from app.db.crud.roles import role_crud
from app.services.base import BaseService


class RoleService(BaseService):
    """Сервис для бизнес-логики ролей."""

    def __init__(self) -> None:
        """Инициализировать сервис ролей."""
        super().__init__()
        self.crud = role_crud

    async def get_roles(self, session: AsyncSession) -> list[RoleResponse]:
        """Получить список всех ролей.

        Args:
            session: Сессия базы данных

        Returns:
            Список ролей
        """
        roles = await self.crud.find_all(session)
        return [RoleResponse.model_validate(role, from_attributes=True) for role in roles]

    async def get_role_by_id(self, session: AsyncSession, role_id: int) -> RoleResponse:
        """Получить роль по ID.

        Args:
            session: Сессия базы данных
            role_id: ID роли

        Returns:
            Роль

        Raises:
            HTTPException: Если роль не найдена
        """
        role = await self.crud.find_one_or_none(session, id=role_id)
        if not role:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f'Роль с id {role_id} не найдена',
            )
        return RoleResponse.model_validate(role, from_attributes=True)
