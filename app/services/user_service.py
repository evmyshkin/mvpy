"""Сервис для работы с пользователями."""

from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_400_BAD_REQUEST
from starlette.status import HTTP_404_NOT_FOUND
from starlette.status import HTTP_409_CONFLICT

from app.api.v1.schemas.users import UserCreateRequest
from app.api.v1.schemas.users import UserCreateResponse
from app.api.v1.schemas.users import UserUpdateRequest
from app.api.v1.schemas.users import UserUpdateResponse
from app.db.crud.users import UsersCrud
from app.services.base import BaseService
from app.services.error_messages import ErrorMessages

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
        """Инициализировать сервис пользователей."""
        super().__init__()
        self.crud = UsersCrud()

    async def create_user(
        self,
        session: AsyncSession,
        user_data: UserCreateRequest,
    ) -> UserCreateResponse:
        """Создать нового пользователя.

        Args:
            session: Асинхронная сессия БД
            user_data: Данные для создания пользователя

        Returns:
            Схема созданного пользователя

        Raises:
            HTTPException: Если email уже существует (409)
        """
        # Проверка существования email
        if await self.crud.email_exists(session, user_data.email):
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=ErrorMessages.USER_EMAIL_EXISTS.value,
            )

        # Подготовка данных для создания пользователя
        user_dict = user_data.model_dump()
        user_dict['password_hash'] = hash_password(user_data.password)
        del user_dict['password']
        del user_dict['repeat_password']

        # Создание пользователя
        try:
            user = await self.crud.add_one(session, **user_dict)
        except IntegrityError as err:
            # Защита от race condition
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=ErrorMessages.USER_EMAIL_EXISTS.value,
            ) from err

        return UserCreateResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
        )

    async def update_user(
        self,
        session: AsyncSession,
        user_id: int,
        user_data: UserUpdateRequest,
    ) -> UserUpdateResponse:
        """Обновить данные пользователя.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя для обновления
            user_data: Данные для обновления пользователя

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
                detail=ErrorMessages.USER_NOT_FOUND.value,
            )

        # Проверка уникальности email, если он предоставлен и отличается от текущего
        if (
            user_data.email is not None
            and user_data.email != user.email
            and await self.crud.email_exists(session, user_data.email)
        ):
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail=ErrorMessages.USER_EMAIL_EXISTS.value,
            )

        # Подготовка данных для обновления через model_dump
        # exclude_unset=True исключает неустановленные поля
        # exclude_none=True дополнительно исключает поля с None значениями
        # exclude={'repeat_password'} исключает поле подтверждения пароля
        values = user_data.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude={'repeat_password'},
        )

        # Преобразуем password в password_hash если пароль предоставлен
        if 'password' in values and values['password'] is not None:
            values['password_hash'] = hash_password(values.pop('password'))

        # Обновление пользователя
        updated_user = await self.crud.update_one_or_none(
            session,
            filter_by={'id': user_id},
            values=values,
        )

        if updated_user is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=ErrorMessages.USER_NOT_FOUND.value,
            )

        return UserUpdateResponse(
            id=updated_user.id,
            email=updated_user.email,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            is_active=updated_user.is_active,
        )

    async def deactivate_user(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> None:
        """Деактивировать пользователя по ID.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя для деактивации

        Raises:
            HTTPException: Если пользователь не найден (404)
            HTTPException: Если пользователь уже деактивирован (404)
        """
        # Проверяем что пользователь существует и активен
        user = await self.crud.find_one_or_none(session, id=user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=ErrorMessages.USER_NOT_FOUND.value,
            )

        # Деактивируем пользователя
        await self.crud.update_one_or_none(
            session,
            filter_by={'id': user_id},
            values={'is_active': False},
        )

    async def get_user_by_id(
        self,
        session: AsyncSession,
        user_id: int,
    ) -> UserUpdateResponse:
        """Найти пользователя по ID.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя для поиска

        Returns:
            Схема найденного пользователя

        Raises:
            HTTPException: Если пользователь с указанным ID не найден (404)
        """
        user = await self.crud.find_one_or_none(session, id=user_id)

        if user is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=ErrorMessages.USER_NOT_FOUND.value,
            )

        return UserUpdateResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
        )

    async def search_user_by_email(
        self,
        session: AsyncSession,
        email: str,
    ) -> UserUpdateResponse:
        """Найти пользователя по email.

        Args:
            session: Асинхронная сессия БД
            email: Email пользователя для поиска

        Returns:
            Схема найденного пользователя

        Raises:
            HTTPException: Если пользователь с указанным email не найден (404)
        """
        user = await self.crud.find_by_email_case_insensitive(session, email)

        if user is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail='Пользователь с указанным email не найден',
            )

        return UserUpdateResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
        )

    async def get_all_users(
        self,
        session: AsyncSession,
    ) -> list[UserUpdateResponse]:
        """Получить список всех пользователей.

        Args:
            session: Асинхронная сессия БД

        Returns:
            Список схем пользователей
        """
        users = await self.crud.find_all_users(session)

        return [
            UserUpdateResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
            )
            for user in users
        ]
