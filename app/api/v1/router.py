from fastapi import APIRouter

from app.api.v1.controllers.users import router as users_router

v1_router = APIRouter()


v1_router.include_router(
    users_router,
    prefix='/users',
)
