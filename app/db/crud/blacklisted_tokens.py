"""CRUD для BlacklistedToken."""

from app.db.crud.base import BaseCrud
from app.db.models.blacklisted_token import BlacklistedToken


class BlacklistedTokenCrud(BaseCrud[BlacklistedToken]):
    """CRUD операции для модели BlacklistedToken."""

    def __init__(self) -> None:
        super().__init__(BlacklistedToken)
