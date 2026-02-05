from fastapi import APIRouter

from app.api.extra.healthcheck import router as healthcheck_router
from app.api.v1.router import v1_router

main_router = APIRouter()

# Хелсчек
main_router.include_router(
    healthcheck_router,
    prefix='',
    tags=['healthcheck'],
)

# v1
main_router.include_router(
    v1_router,
    prefix='/api/v1',
    tags=['v1'],
)
