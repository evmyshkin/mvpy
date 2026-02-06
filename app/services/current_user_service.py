"""Сервис для получения и проверки текущего пользователя."""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

from app.api.utils.enums.auth import AuthErrorMessage
from app.db.crud.users import UsersCrud
from app.db.models.user import User
from app.services.base import BaseService


class CurrentUserService(BaseService):
    """Сервис для получения текущего пользователя из БД."""

    def __init__(self) -> None:
        """Инициализировать сервис текущего пользователя."""
        super().__init__()
        self.users_crud = UsersCrud()

    async def get_current_user(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> User:
        """Получить пользователя по ID с проверкой активности.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя из JWT токена

        Returns:
            Объект User

        Raises:
            HTTPException: 401 если пользователь не найден или неактивен
        """
        user = await self.users_crud.find_one_or_none(session, id=user_id)

        if user is None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=AuthErrorMessage.USER_NOT_FOUND,
            )

        if not user.is_active:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=AuthErrorMessage.INACTIVE_USER,
            )

        return user
