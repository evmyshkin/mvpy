"""FastAPI приложение c системой аутентификации и авторизации."""

import uvicorn

from fastapi import FastAPI

from app.api.router import main_router as main_router
from app.config import config

# Fastapi. Запускаем приложение.
app = FastAPI()
app.include_router(main_router)

if __name__ == '__main__':
    uvicorn.run(app, host=config.app.host, port=config.app.port)
