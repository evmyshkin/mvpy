"""Модель BlacklistedToken для отзыва JWT токенов."""

from datetime import UTC
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.base import BaseDBModel


class BlacklistedToken(BaseDBModel):
    """Модель для отозванных JWT токенов.

    Используется для реализации функции выхода из системы (logout).
    Когда пользователь выходит из системы, его токен добавляется в эту таблицу.
    При последующих запросах проверяется, нет ли токена в чёрном списке.
    """

    __tablename__ = 'blacklisted_tokens'

    token_jti: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment='Уникальный идентификатор токена (JWT ID)',
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment='ID пользователя, которому был выдан токен',
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        comment='Время отзыва токена',
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment='Время истечения токена (из JWT exp claim)',
    )

    __table_args__ = (Index('idx_blacklisted_tokens_expires_at', 'expires_at'),)
