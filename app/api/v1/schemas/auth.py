"""Pydantic схемы для аутентификации и авторизации."""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field

from app.api.utils.enums.auth import AuthErrorMessage
from app.api.utils.enums.auth import TokenDetail


class AuthRequest(BaseModel):
    """Схема запроса на аутентификацию."""

    email: EmailStr = Field(..., description='Email пользователя')
    password: str = Field(..., min_length=8, description='Пароль пользователя')

    model_config = ConfigDict(
        json_schema_extra={
            'examples': [
                {
                    'email': 'user@example.com',
                    'password': 'Password123',
                },
            ],
        },
    )


class AuthResponse(BaseModel):
    """Схема ответа с JWT токеном."""

    access_token: str = Field(..., description='JWT токен доступа')
    token_type: str = Field(default=TokenDetail.BEARER, description='Тип токена')
    expires_in: int = Field(..., description='Время жизни токена в секундах')

    model_config = ConfigDict(
        json_schema_extra={
            'examples': [
                {
                    'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                    'token_type': 'bearer',
                    'expires_in': 3600,
                },
            ],
        },
    )


class LogoutResponse(BaseModel):
    """Схема ответа на выход из системы."""

    message: str = Field(default=AuthErrorMessage.LOGOUT_SUCCESS, description='Сообщение об успехе')

    model_config = ConfigDict(
        json_schema_extra={
            'examples': [
                {'message': 'Успешный выход из системы'},
            ],
        },
    )
