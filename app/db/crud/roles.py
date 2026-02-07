"""CRUD операции для Role модели."""

from app.db.crud.base import BaseCrud
from app.db.models.role import Role


class RoleCrud(BaseCrud[Role]):
    """CRUD операции для ролевой модели."""

    def __init__(self) -> None:
        super().__init__(Role)


role_crud = RoleCrud()
