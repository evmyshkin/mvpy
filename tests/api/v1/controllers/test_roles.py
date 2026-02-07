"""Тесты для roles API endpoints."""

import pytest

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_roles_returns_3_roles(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Тест GET /api/v1/roles/ возвращает 3 роли.

    Args:
        async_client: Асинхронный HTTP клиент
        auth_headers: Заголовки авторизации
    """
    response = await async_client.get(
        '/api/v1/roles/',
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Проверяем что возвращается список
    assert isinstance(data, list)
    assert len(data) == 3

    # Проверяем структуру каждой роли
    for role in data:
        assert 'id' in role
        assert isinstance(role['id'], int)
        assert 'name' in role
        assert isinstance(role['name'], str)
        assert 'description' in role
        assert 'created_at' in role
        assert 'updated_at' in role

    # Проверяем наличие трёх ролей с уникальными id
    role_ids = {role['id'] for role in data}
    assert len(role_ids) == 3  # Все id уникальны

    # Проверяем наличие ожидаемых ролей
    role_names = {role['name'] for role in data}
    assert 'user' in role_names
    assert 'manager' in role_names
    assert 'admin' in role_names


@pytest.mark.asyncio
async def test_get_roles_unauthorized(
    async_client: AsyncClient,
) -> None:
    """Тест GET /api/v1/roles/ без токена авторизации.

    Args:
        async_client: Асинхронный HTTP клиент
    """
    response = await async_client.get('/api/v1/roles/')

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_role_by_id_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Тест GET /api/v1/roles/{id}/ возвращает роль по ID.

    Args:
        async_client: Асинхронный HTTP клиент
        auth_headers: Заголовки авторизации
    """
    # Тестируем получение роли user (id=1)
    response = await async_client.get(
        '/api/v1/roles/1',
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Проверяем структуру ответа
    assert data['id'] == 1
    assert data['name'] == 'user'
    assert 'description' in data
    assert 'created_at' in data
    assert 'updated_at' in data


@pytest.mark.asyncio
async def test_get_role_by_id_not_found(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Тест GET /api/v1/roles/{id}/ для несуществующей роли.

    Args:
        async_client: Асинхронный HTTP клиент
        auth_headers: Заголовки авторизации
    """
    response = await async_client.get(
        '/api/v1/roles/999',
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert 'не найдена' in response.json()['detail']


@pytest.mark.asyncio
async def test_get_role_by_id_unauthorized(
    async_client: AsyncClient,
) -> None:
    """Тест GET /api/v1/roles/{id}/ без токена авторизации.

    Args:
        async_client: Асинхронный HTTP клиент
    """
    response = await async_client.get('/api/v1/roles/1')

    assert response.status_code == 401
