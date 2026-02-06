"""Контроллеры для аутентификации и авторизации."""

from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_token_data
from app.api.v1.schemas.auth import AuthRequest
from app.api.v1.schemas.auth import AuthResponse
from app.api.v1.schemas.auth import LogoutResponse
from app.db.session import DBConnector
from app.services.auth_service import AuthService

router = APIRouter(prefix='/auth', tags=['auth'])

# Инициализация сервиса
auth_service = AuthService()


@router.post('/login', response_model=AuthResponse)
async def login(
    auth_data: AuthRequest,
    session: AsyncSession = Depends(DBConnector().get_session),
) -> AuthResponse:
    """Аутентифицировать пользователя по email и паролю.

    Args:
        auth_data: Email и пароль для аутентификации
        session: Асинхронная сессия БД

    Returns:
        AuthResponse с JWT токеном

    Raises:
        HTTPException: 401 если неверный email/пароль или пользователь неактивен
    """
    return await auth_service.authenticate(session=session, auth_data=auth_data)


@router.post('/logout', response_model=LogoutResponse)
async def logout(
    token_data: tuple[str, int, datetime] = Depends(get_token_data),
    session: AsyncSession = Depends(DBConnector().get_session),
) -> LogoutResponse:
    """Выйти из системы путём добавления токена в чёрный список.

    Args:
        token_data: Кортеж (token_jti, user_id, expires_at) из JWT токена
        session: Асинхронная сессия БД

    Returns:
        LogoutResponse с сообщением об успешном выходе

    Raises:
        HTTPException: 401 если токен отсутствует, невалиден или уже отозван
    """
    token_jti, user_id, expires_at = token_data

    return await auth_service.logout(
        session=session,
        token_jti=token_jti,
        user_id=user_id,
        token_expires_at=expires_at,
    )
