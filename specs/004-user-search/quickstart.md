# Quickstart Guide: Поиск пользователей через API

**Feature**: Поиск пользователей через API
**Branch**: `004-user-search`
**Date**: 2025-02-06

## Обзор фичи

Эта фича добавляет API endpoint для поиска пользователей в системе. Поддерживаются два сценария:

1. **Поиск по email**: Найти конкретного пользователя по email адресу
2. **Получение всех пользователей**: Получить список всех зарегистрированных пользователей

**Безопасность**: Пароли пользователей никогда не возвращаются в API ответах.

---

## Структура изменений

```
app/
├── api/v1/
│   ├── controllers/users.py          # ✨ Новый GET / endpoint
│   └── schemas/users.py              # ✨ Новые схемы ответа
├── db/
│   └── crud/users.py                 # ✨ Новые CRUD методы
└── services/user_service.py          # ✨ Новые методы поиска

tests/
├── api/v1/controllers/test_users.py  # ✨ Тесты для GET endpoint
└── services/test_user_service.py     # ✨ Тесты для поиска
```

**Примечание**: Модель User не изменяется, миграции БД не требуются.

---

## Разработка

### 1. Запуск тестовой БД

```bash
# Запуск PostgreSQL через Docker Compose
make up

# Или используйте существующую локальную БД
```

### 2. Создание тестовых данных

```python
# Создайте несколько пользователей для тестирования
from app.services.user_service import UserService
from app.api.v1.schemas.users import UserCreateRequest
from app.db.session import connector

async def create_test_users():
    async with connector.get_session() as db:
        service = UserService()

        # Пользователь 1
        await service.create_user(
            db,
            UserCreateRequest(
                email="ivan@example.com",
                first_name="Иван",
                last_name="Иванов",
                password="Password123"
            )
        )

        # Пользователь 2
        await service.create_user(
            db,
            UserCreateRequest(
                email="petr@example.com",
                first_name="Петр",
                last_name="Петров",
                password="Password456"
            )
        )
```

### 3. Тестирование endpoint

**Запуск сервера**:
```bash
# Режим разработки с hot reload
make dev

# Или обычный запуск
uv run uvicorn app.main:app --reload
```

**Тестирование через curl**:

```bash
# Поиск пользователя по email
curl "http://localhost:8000/api/v1/users/?email=ivan@example.com"

# Получение всех пользователей
curl "http://localhost:8000/api/v1/users/"

# Поиск без учета регистра
curl "http://localhost:8000/api/v1/users/?email=IVAN@EXAMPLE.COM"

# Тест ошибки 404 (пользователь не найден)
curl "http://localhost:8000/api/v1/users/?email=notfound@example.com"

# Тест ошибки 422 (невалидный email)
curl "http://localhost:8000/api/v1/users/?email=invalid-email"
```

**Тестирование через браузер**:
- Откройте `http://localhost:8000/docs` для интерактивной документации Swagger UI
- Откройте `http://localhost:8000/redoc` для альтернативной документации

---

## Тестирование

### Запуск всех тестов

```bash
# Все тесты с покрытием
make test

# Или напрямую
pytest --cov=app --cov-branch --cov-report=term-missing
```

### Запуск конкретных тестов

```bash
# Тесты для контроллера users
pytest tests/api/v1/controllers/test_users.py -v

# Тесты для сервиса
pytest tests/services/test_user_service.py -v

# Конкретный тест
pytest tests/api/v1/controllers/test_users.py::test_search_user_by_email_success -v

# Тесты с выводом print statements
pytest -s tests/api/v1/controllers/test_users.py
```

### Покрытие кода

```bash
# Покрытие с HTML отчетом
pytest --cov=app --cov-branch --cov-report=html

# Откройте отчет в браузере
open htmlcov/index.html
```

**Ожидаемое покрытие**: >85% (в соответствии с существующими тестами в проекте)

---

## API Примеры

### Пример 1: Поиск пользователя

**Request**:
```http
GET /api/v1/users/?email=ivan@example.com HTTP/1.1
Host: localhost:8000
```

**Response** (200 OK):
```json
{
  "id": 1,
  "email": "ivan@example.com",
  "first_name": "Иван",
  "last_name": "Иванов"
}
```

### Пример 2: Список всех пользователей

**Request**:
```http
GET /api/v1/users/ HTTP/1.1
Host: localhost:8000
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "email": "ivan@example.com",
    "first_name": "Иван",
    "last_name": "Иванов"
  },
  {
    "id": 2,
    "email": "petr@example.com",
    "first_name": "Петр",
    "last_name": "Петров"
  }
]
```

### Пример 3: Пользователь не найден

**Request**:
```http
GET /api/v1/users/?email=notfound@example.com HTTP/1.1
Host: localhost:8000
```

**Response** (404 Not Found):
```json
{
  "detail": "Пользователь с указанным email не найден"
}
```

---

## Проверка качества кода

### Pre-commit hooks

```bash
# Запуск всех проверок
pre-commit run --all-files

# Или только для измененных файлов
git add .
pre-commit run
```

**Проверки**:
- Ruff (линтер и форматирование)
- MyPy (проверка типов)
- Тесты (pytest)

### Ручные проверки

```bash
# Линтер
ruff check app/ tests/

# Форматирование
ruff format app/ tests/

# Типизация
mypy app/
```

---

## Процесс имплементации

### Шаг 1: CRUD слой

**Файл**: `app/db/crud/users.py`

```python
# Добавить методы в класс UsersCrud:

async def find_by_email_case_insensitive(
    self, session: AsyncSession, email: str
) -> User | None:
    """Найти пользователя по email без учета регистра."""
    stmt = select(User).where(func.lower(User.email) == func.lower(email))
    result = await session.execute(stmt)
    return result.scalars().first()

async def find_all_users(self, session: AsyncSession) -> list[User]:
    """Получить список всех пользователей."""
    stmt = select(User)
    result = await session.execute(stmt)
    return list(result.scalars().all())
```

### Шаг 2: Schema слой

**Файл**: `app/api/v1/schemas/users.py`

```python
# Добавить новые схемы:

class UserSearchResponse(BaseModel):
    """Схема ответа при поиске пользователя."""

    id: int
    email: str
    first_name: str
    last_name: str
    # password_hash отсутствует для безопасности
```

### Шаг 3: Service слой

**Файл**: `app/services/user_service.py`

```python
# Добавить методы в класс UserService:

async def search_user_by_email(
    self, session: AsyncSession, email: str
) -> UserSearchResponse:
    """Найти пользователя по email."""
    user = await self.crud.find_by_email_case_insensitive(session, email)

    if user is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Пользователь с указанным email не найден'
        )

    return UserSearchResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name
    )

async def get_all_users(
    self, session: AsyncSession
) -> list[UserSearchResponse]:
    """Получить список всех пользователей."""
    users = await self.crud.find_all_users(session)

    return [
        UserSearchResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name
        )
        for user in users
    ]
```

### Шаг 4: Controller слой

**Файл**: `app/api/v1/controllers/users.py`

```python
# Добавить новый endpoint:

@router.get("/")
async def search_users(
    email: EmailStr | None = None,
    db: AsyncSession = Depends(connector.get_session),
) -> UserSearchResponse | list[UserSearchResponse]:
    """Поиск пользователей.

    Если указан email - возвращает одного пользователя.
    Если email не указан - возвращает список всех пользователей.
    """
    service = UserService()

    if email is not None:
        return await service.search_user_by_email(db, email)

    return await service.get_all_users(db)
```

### Шаг 5: Тесты

**Файл**: `tests/api/v1/controllers/test_users.py`

```python
# Добавить тесты для всех сценариев:
# - Успешный поиск по email
# - Поиск без учета регистра
# - Пользователь не найден (404)
# - Невалидный email (422)
# - Получение списка всех пользователей
# - Пустой список пользователей
```

**Файл**: `tests/services/test_user_service.py`

```python
# Добавить тесты для сервисных методов:
# - search_user_by_email: успех
# - search_user_by_email: пользователь не найден
# - get_all_users: несколько пользователей
# - get_all_users: пустой список
```

---

## Полезные команды

```bash
# Применить миграции (если понадобятся в будущем)
alembic upgrade head

# Откатить миграции
alembic downgrade -1

# Создать новую миграцию
alembic revision --autogenerate -m "description"

# Проверить статус БД
alembic current
alembic history

# Посмотреть открытые файлы в IDE
# (для JetBrains IDE)
```

---

## Troubleshooting

### Проблема: Тесты падают с ошибкой БД

**Решение**:
```bash
# Пересоздать тестовую БД
docker-compose down -v
docker-compose up -d

# Или применить миграции
alembic upgrade head
```

### Проблема: Email не находится (case-sensitive)

**Проверка**: Убедитесь, что используется `func.lower()` или `ilike` в CRUD методе

### Проблема: Пароль возвращается в ответе

**Проверка**: Убедитесь, что Pydantic схема `UserSearchResponse` не содержит поле `password_hash`

### Проблема: 422 ошибка на валидный email

**Проверка**: Убедитесь, что используется тип `EmailStr` от Pydantic, а не просто `str`

---

## Следующие шаги

После завершения имплементации:

1. ✅ Запустите `make test` - все тесты должны проходить
2. ✅ Запустите `pre-commit run --all-files` - все проверки должны проходить
3. ✅ Проверьте покрытие кода (должно быть >85%)
4. ✅ Протестируйте вручную через Swagger UI (`/docs`)
5. ✅ Перейдите к следующей фиче или создайте Pull Request

---

## Дополнительная документация

- [Конституция проекта](../../../.specify/memory/constitution.md)
- [Спецификация фичи](./spec.md)
- [План имплементации](./plan.md)
- [Research](./research.md)
- [Data Model](./data-model.md)
- [API Contracts](./contracts/api.md)

---

**Удачи с разработкой!** 🚀