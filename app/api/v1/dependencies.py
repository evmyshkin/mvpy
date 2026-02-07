"""Dependency functions для API v1."""

from datetime import datetime

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.session import DBConnector
from app.services.current_user_service import CurrentUserService
from app.services.token_service import TokenService

# OAuth2 схема для Bearer токена
oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(DBConnector().get_session),
) -> User:  # TODO: shadows the CurrentUserService method name, consider renaming
    """Получить текущего пользователя из JWT токена.

    Args:
        credentials: JWT токен из заголовка Authorization
        session: Асинхронная сессия БД

    Returns:
        Объект User

    Raises:
        HTTPException: 401 если токен отсутствует, невалиден, истёк,
                     отозван или пользователь неактивен
    """
    token_service = TokenService()
    current_user_service = CurrentUserService()

    # Валидация токена и получение user_id
    _, user_id, _ = await token_service.validate_token(
        session=session,
        credentials=credentials,
    )

    # Получение пользователя из БД с проверкой is_active
    user = await current_user_service.get_current_user(session=session, user_id=user_id)

    return user


async def get_token_data(
    credentials: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(DBConnector().get_session),
) -> tuple[str, int, datetime]:
    """Получить данные токена для операции logout.

    Args:
        credentials: JWT токен из заголовка Authorization
        session: Асинхронная сессия БД

    Returns:
        Кортеж (token_jti, user_id, expires_at)

    Raises:
        HTTPException: 401 если токен отсутствует, невалиден, истёк или отозван
    """
    token_service = TokenService()
    return await token_service.validate_token(session=session, credentials=credentials)
