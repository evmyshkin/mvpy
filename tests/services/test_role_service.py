"""Тесты для RoleService."""

import pytest

from fastapi import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from app.services.role_service import RoleService


@pytest.mark.asyncio
async def test_get_roles_returns_all_roles(
    db_session,
    role_service: RoleService,
) -> None:
    """Тест RoleService get_roles возвращает все роли.

    Args:
        db_session: Тестовая сессия БД
        role_service: Сервис ролей
    """
    roles = await role_service.get_roles(session=db_session)

    # Проверяем что возвращается список
    assert isinstance(roles, list)
    assert len(roles) == 3

    # Проверяем структуру каждой роли
    for role in roles:
        assert hasattr(role, 'id')
        assert isinstance(role.id, int)
        assert hasattr(role, 'name')
        assert isinstance(role.name, str)
        assert hasattr(role, 'description')
        assert hasattr(role, 'created_at')
        assert hasattr(role, 'updated_at')

    # Проверяем наличие трёх ролей с уникальными id
    role_ids = {role.id for role in roles}
    assert len(role_ids) == 3  # Все id уникальны

    # Проверяем наличие ожидаемых ролей
    role_names = {role.name for role in roles}
    assert 'user' in role_names
    assert 'manager' in role_names
    assert 'admin' in role_names


@pytest.mark.asyncio
async def test_get_role_by_id_success(
    db_session,
    role_service: RoleService,
) -> None:
    """Тест RoleService get_role_by_id возвращает роль по ID.

    Args:
        db_session: Тестовая сессия БД
        role_service: Сервис ролей
    """
    # Тестируем получение роли user (id=1)
    role = await role_service.get_role_by_id(session=db_session, role_id=1)

    # Проверяем структуру ответа
    assert role.id == 1
    assert role.name == 'user'
    assert role.description is not None
    assert hasattr(role, 'created_at')
    assert hasattr(role, 'updated_at')


@pytest.mark.asyncio
async def test_get_role_by_id_manager(
    db_session,
    role_service: RoleService,
) -> None:
    """Тест RoleService get_role_by_id для роли manager.

    Args:
        db_session: Тестовая сессия БД
        role_service: Сервис ролей
    """
    role = await role_service.get_role_by_id(session=db_session, role_id=2)

    assert role.id == 2
    assert role.name == 'manager'


@pytest.mark.asyncio
async def test_get_role_by_id_admin(
    db_session,
    role_service: RoleService,
) -> None:
    """Тест RoleService get_role_by_id для роли admin.

    Args:
        db_session: Тестовая сессия БД
        role_service: Сервис ролей
    """
    role = await role_service.get_role_by_id(session=db_session, role_id=3)

    assert role.id == 3
    assert role.name == 'admin'


@pytest.mark.asyncio
async def test_get_role_by_id_not_found(
    db_session,
    role_service: RoleService,
) -> None:
    """Тест RoleService get_role_by_id для несуществующей роли.

    Args:
        db_session: Тестовая сессия БД
        role_service: Сервис ролей
    """
    with pytest.raises(HTTPException) as exc_info:
        await role_service.get_role_by_id(session=db_session, role_id=999)

    assert exc_info.value.status_code == HTTP_404_NOT_FOUND
    assert 'не найдена' in exc_info.value.detail
