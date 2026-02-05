"""CRUD операции для пользователей."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.base import BaseCrud
from app.db.models.user import User


class UsersCrud(BaseCrud[User]):
    """CRUD операции для пользователей."""

    def __init__(self) -> None:
        super().__init__(User)

    async def find_by_email(self, session: AsyncSession, email: str) -> User | None:
        """Найти пользователя по email.

        Args:
            session: Асинхронная сессия БД
            email: Email пользователя

        Returns:
            Объект User или None если не найден
        """
        return await self.find_one_or_none(session, email=email)

    async def email_exists(self, session: AsyncSession, email: str) -> bool:
        """Проверить существование email.

        Args:
            session: Асинхронная сессия БД
            email: Email для проверки

        Returns:
            True если email существует, False иначе
        """
        return await self.find_by_email(session, email) is not None
