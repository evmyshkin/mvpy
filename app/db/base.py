"""Базовая модель SQLAlchemy для всех ORM моделей."""

from sqlalchemy import Integer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class BaseDBModel(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей БД."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
