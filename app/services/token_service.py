"""Сервис для валидации JWT токенов и получения текущего пользователя."""

from datetime import UTC
from datetime import datetime

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

from app.api.utils.enums.auth import AuthErrorMessage
from app.config import config
from app.db.crud.blacklisted_tokens import BlacklistedTokenCrud
from app.services.base import BaseService


class TokenService(BaseService):
    """Сервис для валидации JWT токенов."""

    def __init__(self) -> None:
        """Инициализировать сервис токенов."""
        super().__init__()
        self.blacklist_crud = BlacklistedTokenCrud()

    async def validate_token(
        self,
        session: AsyncSession,
        credentials: HTTPAuthorizationCredentials | None,
    ) -> tuple[str, int, datetime]:
        """Валидировать JWT токен и извлечь данные пользователя.

        Args:
            session: Асинхронная сессия БД
            credentials: JWT токен из заголовка Authorization

        Returns:
            Кортеж (token_jti, user_id, expires_at)

        Raises:
            HTTPException: 401 если токен отсутствует, невалиден, истёк или отозван
        """
        # Проверка наличия токена
        if credentials is None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=AuthErrorMessage.MISSING_TOKEN,
                headers={'WWW-Authenticate': 'Bearer'},
            )

        token = credentials.credentials

        try:
            # Декодирование токена
            payload = jwt.decode(
                token,
                config.jwt.secret_key,
                algorithms=[config.jwt.algorithm],
            )
        except JWTError as err:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=AuthErrorMessage.INVALID_TOKEN,
                headers={'WWW-Authenticate': 'Bearer'},
            ) from err

        # Извлечение данных из токена
        token_jti: str = payload.get('jti')
        user_id: int = payload.get('user_id')
        exp_timestamp = payload.get('exp')
        exp: datetime = datetime.fromtimestamp(exp_timestamp, tz=UTC)

        # Конвертируем в naive datetime для PostgreSQL (без timezone info)
        exp_naive = exp.replace(tzinfo=None)

        if token_jti is None or user_id is None or exp is None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=AuthErrorMessage.INVALID_TOKEN,
                headers={'WWW-Authenticate': 'Bearer'},
            )

        # Проверка, не отозван ли токен
        blacklisted_token = await self.blacklist_crud.find_one_or_none(
            session,
            token_jti=token_jti,
        )
        if blacklisted_token is not None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=AuthErrorMessage.REVOKED_TOKEN,
                headers={'WWW-Authenticate': 'Bearer'},
            )

        return token_jti, user_id, exp_naive
