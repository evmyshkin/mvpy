"""Enum'ы для сообщений об ошибках аутентификации."""

from enum import StrEnum


class AuthErrorMessage(StrEnum):
    """Сообщения об ошибках аутентификации и авторизации."""

    INVALID_CREDENTIALS = 'Неверный email или пароль'
    INACTIVE_USER = 'Учётная запись неактивна'
    MISSING_TOKEN = 'Отсутствует токен авторизации'
    INVALID_TOKEN = 'Невалидный токен авторизации'
    EXPIRED_TOKEN = 'Срок действия токена истёк'
    REVOKED_TOKEN = 'Токен отозван'
    TOKEN_ALREADY_BLACKLISTED = 'Токен уже отозван'
    LOGOUT_SUCCESS = 'Успешный выход из системы'
    USER_NOT_FOUND = 'Пользователь не найден'


class TokenDetail(StrEnum):
    """Детали токена для ответов API."""

    BEARER = 'bearer'
