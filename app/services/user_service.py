"""Сервис для работы с пользователями."""

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.status import HTTP_404_NOT_FOUND
from starlette.status import HTTP_409_CONFLICT

from app.api.v1.schemas.users import UserCreateResponse
from app.api.v1.schemas.users import UserUpdateResponse
from app.db.crud.users import UsersCrud
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
        except IntegrityError as err:
            # Защита от race condition
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail='Пользователь с таким email уже существует',
            ) from err

        return UserCreateResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )

    async def update_user(
        self,
        session: AsyncSession,
        user_id: int,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        password: str | None = None,
    ) -> UserUpdateResponse:
        """Обновить данные пользователя.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя для обновления
            email: Новый email (опционально)
            first_name: Новое имя (опционально)
            last_name: Новая фамилия (опционально)
            password: Новый пароль в открытом виде (опционально)

        Returns:
            Схема обновлённого пользователя

        Raises:
            HTTPException: Если пользователь не найден (404)
            HTTPException: Если email уже занят другим пользователем (400)
        """
        # Проверка существования пользователя
        user = await self.crud.find_one_or_none(session, id=user_id)
        if user is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail='Пользователь не найден',
            )

        # Проверка уникальности email, если он предоставлен и отличается от текущего
        if (
            email is not None
            and email != user.email
            and await self.crud.email_exists(session, email)
        ):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail='Пользователь с таким email уже существует',
            )

        # Подготовка словаря обновляемых полей
        values: dict[str, object] = {}
        if email is not None:
            values['email'] = email
        if first_name is not None:
            values['first_name'] = first_name
        if last_name is not None:
            values['last_name'] = last_name
        if password is not None:
            values['password_hash'] = hash_password(password)

        # Обновление пользователя
        updated_user = await self.crud.update_one_or_none(
            session,
            filter_by={'id': user_id},
            values=values,
        )

        if updated_user is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail='Пользователь не найден',
            )

        return UserUpdateResponse(
            id=updated_user.id,
            email=updated_user.email,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
        )
