"""Pydantic схемы для пользователей."""

from pydantic import BaseModel, EmailStr, field_validator
import re


class UserCreateRequest(BaseModel):
    """Схема запроса на создание пользователя."""

    email: EmailStr
    first_name: str
    last_name: str
    password: str

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Валидация имени/фамилии.

        Args:
            v: Значение поля (first_name или last_name)

        Returns:
            Валидированное значение

        Raises:
            ValueError: Если значение содержит недопустимые символы
                или превышает 100 символов
        """
        if not re.match(r'^[А-Яа-яA-Za-z\-]+$', v):
            raise ValueError(
                'Должно содержать только русские/английские буквы и тире'
            )
        if len(v) > 100:
            raise ValueError('Длина не должна превышать 100 символов')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """Валидация длины пароля.

        Args:
            v: Значение поля password

        Returns:
            Валидированное значение

        Raises:
            ValueError: Если длина пароля меньше 8 или больше 100 символов
        """
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        if len(v) > 100:
            raise ValueError('Пароль не должен превышать 100 символов')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Валидация сложности пароля.

        Args:
            v: Значение поля password

        Returns:
            Валидированное значение

        Raises:
            ValueError: Если пароль не содержит заглавную букву,
                строчную букву или цифру
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError(
                'Пароль должен содержать минимум 1 заглавную букву'
            )
        if not re.search(r'[a-z]', v):
            raise ValueError(
                'Пароль должен содержать минимум 1 строчную букву'
            )
        if not re.search(r'\d', v):
            raise ValueError('Пароль должен содержать минимум 1 цифру')
        return v


class UserCreateResponse(BaseModel):
    """Схема ответа при создании пользователя."""

    id: int
    email: str
    first_name: str
    last_name: str
