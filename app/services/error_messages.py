"""Enum для сообщений об ошибках сервиса."""

from enum import Enum


class ErrorMessages(str, Enum):
    """Сообщения об ошибках в бизнес-логике."""

    USER_EMAIL_EXISTS = 'Пользователь с таким email уже существует'
    USER_NOT_FOUND = 'Пользователь не найден'
    USER_INVALID_EMAIL_FORMAT = 'Некорректный формат email'
    USER_INVALID_NAME_FORMAT = (
        'Имя и фамилия должны содержать только буквы русского или английского алфавита и дефис'
    )
    USER_WEAK_PASSWORD = (
        'Пароль должен содержать минимум 8 символов, включая заглавную и строчную буквы и цифру'
    )
