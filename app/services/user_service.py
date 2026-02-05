"""Сервис для работы с пользователями."""

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_409_CONFLICT

from app.api.v1.schemas.users import UserCreateResponse
from app.db.crud.users import UsersCrud
from app.db.models.user import User
from app.services.base import BaseService

# Контекст для хеширования паролей с использованием bcrypt
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    """Хешировать пароль с использованием bcrypt.

    Args:
        password: Пароль в открытом виде

    Returns:
        Захешированный пароль
    """
    return pwd_context.hash(password)


class UserService(BaseService):
    """Сервис для бизнес-логики пользователей."""

    def __init__(self) -> None:
        super().__init__()
        self.crud = UsersCrud()

    async def create_user(
        self,
        session: AsyncSession,
        email: str,
        first_name: str,
        last_name: str,
        password: str,
    ) -> UserCreateResponse:
        """Создать нового пользователя.

        Args:
            session: Асинхронная сессия БД
            email: Email пользователя
            first_name: Имя пользователя
            last_name: Фамилия пользователя
            password: Пароль в открытом виде

        Returns:
            Схема созданного пользователя

        Raises:
            HTTPException: Если email уже существует (409)
        """
        # Проверка существования email
        if await self.crud.email_exists(session, email):
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail='Пользователь с таким email уже существует',
            )

        # Хеширование пароля
        password_hash = hash_password(password)

        # Создание пользователя
        try:
            user = await self.crud.add_one(
                session,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password_hash=password_hash,
            )
        except IntegrityError:
            # Защита от race condition
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail='Пользователь с таким email уже существует',
            )

        return UserCreateResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )