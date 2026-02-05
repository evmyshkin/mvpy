# Quickstart: Создание пользователя через API

**Feature**: 001-create-user | **Date**: 2026-02-05

## Запуск проекта

### Локальная разработка

```bash
# Установка зависимостей
uv sync

# Запуск с hot reload
make dev
# или
uv run uvicorn app.main:app --reload

# Проверка healthcheck
curl http://localhost:8000/
```

### Docker

```bash
# Запуск контейнеров
make up

# Проверка healthcheck
curl http://localhost:8000/
```

## API Endpoint

**POST** `/api/v1/users/`

Создаёт нового пользователя в системе.

### Request

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ivan.ivanov@example.com",
    "first_name": "Иван",
    "last_name": "Иванов",
    "password": "Password123"
  }'
```

### Success Response (201 Created)

```json
{
  "id": 1,
  "email": "ivan.ivanov@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "created_at": "2026-02-05T12:34:56.789Z",
  "updated_at": "2026-02-05T12:34:56.789Z"
}
```

Headers:
```
Location: /api/v1/users/1
```

### Error Responses

**409 Conflict** - Email уже существует:
```json
{
  "detail": "Пользователь с таким email уже существует"
}
```

**422 Validation Error** - Невалидные данные:
```json
{
  "detail": [
    {
      "msg": "Пароль должен содержать минимум 8 символов",
      "loc": ["body", "password"],
      "type": "value_error"
    }
  ]
}
```

## Примеры использования

### Python (httpx)

```python
import httpx

async def create_user():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8000/api/v1/users/',
            json={
                'email': 'ivan.ivanov@example.com',
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'password': 'Password123'
            }
        )
        print(response.status_code)  # 201
        print(response.json())  # {"id": 1, "email": ...}
```

### JavaScript (fetch)

```javascript
const response = await fetch('http://localhost:8000/api/v1/users/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'ivan.ivanov@example.com',
    first_name: 'Иван',
    last_name: 'Иванов',
    password: 'Password123'
  })
});

const user = await response.json();
console.log(user);
```

## Тестирование

### Запуск тестов

```bash
# Все тесты с покрытием
make test
# или
pytest --cov=app --cov-branch --cov-report=term-missing

# Только тесты пользователей
pytest tests/api/v1/controllers/test_users.py -v

# С выводом print statements
pytest tests/api/v1/controllers/test_users.py -v -s
```

### Пример теста

```python
import pytest
from httpx import AsyncClient
from faker import Faker

@pytest.mark.asyncio
async def test_create_user_success(async_client: AsyncClient, faker: Faker):
    """Тест успешного создания пользователя."""
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': faker.email(),
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password': 'Password123'
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert 'id' in data
    assert data['email'] == 'ivan@example.com'
    assert 'password' not in data  # Пароль не должен возвращаться

@pytest.mark.asyncio
async def test_create_user_duplicate_email(async_client: AsyncClient):
    """Тест дубликата email."""
    email = 'duplicate@example.com'

    # Первый запрос
    await async_client.post(
        '/api/v1/users/',
        json={
            'email': email,
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password': 'Password123'
        }
    )

    # Второй запрос с тем же email
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': email,
            'first_name': 'Петр',
            'last_name': 'Петров',
            'password': 'Password123'
        }
    )

    assert response.status_code == 409
    assert 'уже существует' in response.json()['detail']

@pytest.mark.asyncio
async def test_create_user_invalid_name(async_client: AsyncClient):
    """Тест невалидного имени (цифры)."""
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': 'test@example.com',
            'first_name': 'Иван1',
            'last_name': 'Иванов',
            'password': 'Password123'
        }
    )

    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_user_weak_password(async_client: AsyncClient):
    """Тест слабого пароля (без заглавной буквы)."""
    response = await async_client.post(
        '/api/v1/users/',
        json={
            'email': 'test@example.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password': 'password123'
        }
    )

    assert response.status_code == 422
    assert 'заглавную' in response.json()['detail'][0]['msg']
```

## Документация API

После запуска сервера доступна автогенерируемая документация:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Полезные команды

```bash
# Проверка качества кода
pre-commit run --all-files

# Форматирование кода
ruff format app/ tests/

# Линтер
ruff check app/ tests/

# Тайпинг
mypy app/

# Создание миграции
alembic revision --autogenerate -m "Create users table"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

## Структура файлов

```
app/
├── api/v1/
│   ├── controllers/
│   │   └── users.py           # POST /api/v1/users/
│   └── schemas/
│       └── users.py           # UserCreateRequest, UserCreateResponse
├── db/
│   ├── crud/
│   │   └── users.py           # UsersCrud extends BaseCrud[User]
│   └── models/
│       └── user.py            # User SQLAlchemy model
└── services/
    └── user_service.py        # UserService extends BaseService
```

## Следующие шаги

После реализации этой фичи можно:
1. Добавить эндпоинт для получения пользователя по ID
2. Добавить эндпоинт для обновления пользователя
3. Добавить аутентификацию через JWT токены
4. Добавить подтверждение email

**Примечание**: Эти функции выходят за scope текущей фичи и требуют отдельной спецификации.