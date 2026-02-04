from fastapi import APIRouter
from starlette.responses import Response

router = APIRouter()


@router.get(
    '/healthcheck',
    response_model_exclude_none=True,
    summary='Ручка хелсчека.',
    description='Ручка хелсчека.',
)
async def healthcheck() -> Response:
    """Хелсчек.

    Returns:
        Response: 200 OK
    """
    return Response(content='OK')
