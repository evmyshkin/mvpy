"""Pydantic схемы для пользователей."""

import re

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import field_validator
from pydantic import model_validator


def validate_name_field(value: str | None) -> str | None:
    """Переиспользуемый валидатор для полей имени и фамилии.

    Проверяет, что значение содержит только буквы кириллицы/латиницы и дефисы,
    а также не превышает 100 символов.

    Args:
        value: Значение поля (first_name или last_name)

    Returns:
        Валидированное значение или None, если передан None

    Raises:
        ValueError: Если значение содержит недопустимые символы
            или превышает 100 символов
    """
    if value is None:
        return value
    if not re.match(r'^[А-Яа-яЁёA-Za-z\-]+$', value):
        raise ValueError('Должно содержать только русские/английские буквы и тире')
    if len(value) > 100:
        raise ValueError('Длина не должна превышать 100 символов')
    return value


def validate_password_length(value: str | None) -> str | None:
    """Переиспользуемый валидатор длины пароля.

    Проверяет, что длина пароля составляет от 8 до 100 символов.

    Args:
        value: Значение поля password

    Returns:
        Валидированное значение или None, если передан None

    Raises:
        ValueError: Если длина пароля меньше 8 или больше 100 символов
    """
    if value is None:
        return value
    if len(value) < 8:
        raise ValueError('Пароль должен содержать минимум 8 символов')
    if len(value) > 100:
        raise ValueError('Пароль не должен превышать 100 символов')
    return value


def validate_password_complexity(value: str | None) -> str | None:
    """Переиспользуемый валидатор сложности пароля.

    Проверяет, что пароль содержит минимум одну заглавную букву,
    одну строчную букву и одну цифру.

    Args:
        value: Значение поля password

    Returns:
        Валидированное значение или None, если передан None

    Raises:
        ValueError: Если пароль не содержит заглавную букву,
            строчную букву или цифру
    """
    if value is None:
        return value
    if not re.search(r'[A-Z]', value):
        raise ValueError('Пароль должен содержать минимум 1 заглавную букву')
    if not re.search(r'[a-z]', value):
        raise ValueError('Пароль должен содержать минимум 1 строчную букву')
    if not re.search(r'\d', value):
        raise ValueError('Пароль должен содержать минимум 1 цифру')
    return value


class UserCreateRequest(BaseModel):
    """Схема запроса на создание пользователя."""

    email: EmailStr
    first_name: str
    last_name: str
    password: str
    repeat_password: str

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
        return validate_name_field(v)

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
        return validate_password_length(v)

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
        return validate_password_complexity(v)

    @model_validator(mode='after')
    def validate_passwords_match(self) -> 'UserCreateRequest':
        """Валидация совпадения паролей.

        Returns:
            Валидированный экземпляр схемы

        Raises:
            ValueError: Если пароли не совпадают
        """
        if self.password != self.repeat_password:
            raise ValueError('Пароли не совпадают')
        return self


class UserCreateResponse(BaseModel):
    """Схема ответа при создании пользователя."""

    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool
    role_id: int


class UserUpdateRequest(BaseModel):
    """Схема запроса на обновление пользователя."""

    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    repeat_password: str | None = None

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Валидация имени/фамилии.

        Args:
            v: Значение поля (first_name или last_name)

        Returns:
            Валидированное значение или None

        Raises:
            ValueError: Если значение содержит недопустимые символы
                или превышает 100 символов
        """
        return validate_name_field(v)

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str | None) -> str | None:
        """Валидация длины пароля.

        Args:
            v: Значение поля password

        Returns:
            Валидированное значение или None

        Raises:
            ValueError: Если длина пароля меньше 8 или больше 100 символов
        """
        return validate_password_length(v)

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v: str | None) -> str | None:
        """Валидация сложности пароля.

        Args:
            v: Значение поля password

        Returns:
            Валидированное значение или None

        Raises:
            ValueError: Если пароль не содержит заглавную букву,
                строчную букву или цифру
        """
        return validate_password_complexity(v)

    @model_validator(mode='after')
    def validate_passwords_match(self) -> 'UserUpdateRequest':
        """Валидация совпадения паролей при обновлении.

        Если указан password, то также должен быть указан repeat_password,
        и они должны совпадать.

        Returns:
            Валидированный экземпляр схемы

        Raises:
            ValueError: Если указан только один из паролей или они не совпадают
        """
        if self.password is not None and self.repeat_password is None:
            raise ValueError('Необходимо подтвердить пароль (repeat_password)')
        if self.repeat_password is not None and self.password is None:
            raise ValueError('Необходимо указать пароль (password)')
        if (
            self.password is not None
            and self.repeat_password is not None
            and self.password != self.repeat_password
        ):
            raise ValueError('Пароли не совпадают')
        return self


class UserUpdateResponse(BaseModel):
    """Схема ответа при обновлении пользователя."""

    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool
    role_id: int
