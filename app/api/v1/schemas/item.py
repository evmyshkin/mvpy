from app.schemas.base import BaseSchema


class ItemUpdateSchema(BaseSchema):
    name: str
    price: float
    is_offer: bool | None = None


class ItemSchema(ItemUpdateSchema):
    id: int
