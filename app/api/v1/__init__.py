"""API v1 роутеры для системы аутентификации и авторизации."""

from fastapi import APIRouter

# Создаём главный роутер для v1 API
api_router = APIRouter(prefix='/api/v1')

# Контроллеры будут добавлены позже после их создания
# Пример:
# from app.api.v1.controllers import auth, users, roles, permissions
# api_router.include_router(auth.router, tags=['Аутентификация'])
# api_router.include_router(users.router, tags=['Пользователи'])
# api_router.include_router(roles.router, tags=['Роли и разрешения'])
