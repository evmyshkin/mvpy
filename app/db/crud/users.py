"""CRUD операции для пользователей."""

from sqlalchemy import and_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.base import BaseCrud
from app.db.models.user import User


class UsersCrud(BaseCrud[User]):
    """CRUD операции для пользователей."""

    def __init__(self) -> None:
        """Инициализировать CRUD для пользователей."""
        super().__init__(User)

    async def find_by_email(self, session: AsyncSession, email: str) -> User | None:
        """Найти активного пользователя по email.

        Деактивированные пользователи (is_active=False) исключаются из поиска.

        Args:
            session: Асинхронная сессия БД
            email: Email пользователя

        Returns:
            Объект User или None если не найден или пользователь деактивирован
        """
        stmt = select(User).where(
            and_(
                User.email == email,
                User.is_active,
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def email_exists(self, session: AsyncSession, email: str) -> bool:
        """Проверить существование email.

        Args:
            session: Асинхронная сессия БД
            email: Email для проверки

        Returns:
            True если email существует, False иначе
        """
        return await self.find_by_email(session, email) is not None

    async def deactivate_by_email(self, session: AsyncSession, email: str) -> User | None:
        """Деактивировать пользователя по email.

        Args:
            session: Асинхронная сессия БД
            email: Email пользователя для деактивации

        Returns:
            Объект User с is_active=False или None если не найден
        """
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user is not None:
            user.is_active = False
            # updated_at автоматически обновится через onupdate=func.now()
            await session.commit()

        return user
