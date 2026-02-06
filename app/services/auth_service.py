"""Сервис для аутентификации и авторизации пользователей."""

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

from app.api.utils.enums.auth import AuthErrorMessage
from app.api.v1.schemas.auth import AuthRequest
from app.api.v1.schemas.auth import AuthResponse
from app.api.v1.schemas.auth import LogoutResponse
from app.config import config
from app.db.crud.blacklisted_tokens import BlacklistedTokenCrud
from app.db.crud.users import UsersCrud
from app.db.models.user import User
from app.services.base import BaseService

# Контекст для хеширования паролей с использованием bcrypt
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class AuthService(BaseService):
    """Сервис для бизнес-логики аутентификации."""

    def __init__(self) -> None:
        """Инициализировать сервис аутентификации."""
        super().__init__()
        self.crud = UsersCrud()
        self.blacklist_crud = BlacklistedTokenCrud()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверить пароль против захешированного значения.

        Args:
            plain_password: Пароль в открытом виде
            hashed_password: Захешированный пароль

        Returns:
            True если пароль верный, False иначе
        """
        return pwd_context.verify(plain_password, hashed_password)

    async def authenticate(
        self,
        session: AsyncSession,
        auth_data: AuthRequest,
    ) -> AuthResponse:
        """Аутентифицировать пользователя по email и паролю.

        Args:
            session: Асинхронная сессия БД
            auth_data: Данные для аутентификации (email, password)

        Returns:
            AuthResponse с JWT токеном

        Raises:
            HTTPException: Если неверный email/пароль или пользователь неактивен
        """
        # Найти пользователя по email (без учета регистра)
        user = await self.crud.find_by_email_case_insensitive(session, auth_data.email)

        # Универсальная проверка: пользователь не найден ИЛИ неверный пароль
        if user is None or not self.verify_password(auth_data.password, user.password_hash):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=AuthErrorMessage.INVALID_CREDENTIALS,
            )

        # Проверка активного статуса пользователя
        if not user.is_active:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=AuthErrorMessage.INACTIVE_USER,
            )

        # Генерация JWT токена
        token = self._create_jwt_token(user)

        return AuthResponse(
            access_token=token,
            token_type='bearer',
            expires_in=config.jwt.access_token_expire_minutes * 60,  # В секундах
        )

    def _create_jwt_token(self, user: User) -> str:
        """Создать JWT токен для пользователя.

        Args:
            user: Объект пользователя

        Returns:
            JWT токен в виде строки
        """
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=config.jwt.access_token_expire_minutes)

        payload = {
            'sub': str(user.id),
            'user_id': user.id,
            'is_active': user.is_active,
            'iat': now,
            'exp': expire,
            'jti': str(uuid4()),
        }

        encoded_jwt = jwt.encode(
            payload,
            config.jwt.secret_key,
            algorithm=config.jwt.algorithm,
        )
        return encoded_jwt

    async def logout(
        self,
        session: AsyncSession,
        token_jti: str,
        user_id: int,
        token_expires_at: datetime,
    ) -> LogoutResponse:
        """Выход пользователя из системы путём добавления токена в чёрный список.

        Args:
            session: Асинхронная сессия БД
            token_jti: Уникальный идентификатор токена (JWT ID)
            user_id: ID пользователя
            token_expires_at: Время истечения токена

        Returns:
            LogoutResponse с сообщением об успешном выходе

        Raises:
            HTTPException: Если токен уже отозван
        """
        # Проверяем, не был ли токен уже отозван
        existing_token = await self.blacklist_crud.find_one_or_none(
            session,
            token_jti=token_jti,
        )
        if existing_token is not None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=AuthErrorMessage.TOKEN_ALREADY_BLACKLISTED,
            )

        # Добавляем токен в чёрный список
        await self.blacklist_crud.add_one(
            session,
            token_jti=token_jti,
            user_id=user_id,
            expires_at=token_expires_at,
        )

        return LogoutResponse()
