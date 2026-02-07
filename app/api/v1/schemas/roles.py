"""Pydantic схемы для ролей."""

from datetime import datetime

from pydantic import BaseModel


class RoleResponse(BaseModel):
    """Схема ответа для роли."""

    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class RoleCreateRequest(BaseModel):
    """Схема запроса на создание роли."""

    name: str
    description: str | None = None
