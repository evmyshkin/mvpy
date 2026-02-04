from fastapi import APIRouter

from app.api.v1.schemas.item import ItemSchema
from app.api.v1.schemas.item import ItemUpdateSchema

router = APIRouter()


@router.get('/{item_id}')
def read_item(item_id: int) -> ItemSchema:
    """Ручка-аглушка GET-метода.

    Получить данные о предмете.
    """
    return ItemSchema(id=item_id, is_offer=True, name='item_name', price=100)


@router.put('/{item_id}')
def update_item(item_id: int, item: ItemUpdateSchema) -> ItemSchema:
    """Ручка-заглушка PUT-метода.

    Обновить данные у предмета.
    """
    return ItemSchema(id=item_id, is_offer=item.is_offer, name=item.name, price=item.price)
