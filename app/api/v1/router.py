from fastapi import APIRouter

from app.api.v1.controllers.items import router as items_router

v1_router = APIRouter()

v1_router.include_router(
    items_router,
    prefix='/items',
)
