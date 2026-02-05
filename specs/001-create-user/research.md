# Research: Создание пользователя через API

**Feature**: 001-create-user | **Date**: 2026-02-05

## Research Summary

Этот документ содержит результаты исследования технических решений для реализации API создания пользователя с требованиями из спецификации. Все неизвестные из Technical Context были разрешены.

## Research Decisions

### 1. Хеширование паролей

**Decision**: Использовать `passlib[bcrypt]` для хеширования паролей

**Rationale**:
- passlib является industry standard для хеширования паролей в Python
- Обеспечивает автоматическую генерацию соли
- bcrypt cost factor 12 (default) обеспечивает баланс между скоростью и безопасностью
- Простая интеграция с Pydantic через field_validator

**Alternatives considered**:
- `bcrypt` напрямую: менее удобный API, требуется ручное управление солью
- `argon2`: более современный алгоритм, но менее совместим с существующими системами

**Implementation**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)
```

---

### 2. Валидация first_name/last_name (русские/английские буквы и тире)

**Decision**: Использовать Pydantic V2 @field_validator с regex pattern

**Rationale**:
- Pydantic 2.x имеет новый API для валидаторов
- Regex обеспечивает понятные error messages
- Аннотированная типизация с `Annotated[str, Field(...)]`

**Alternatives considered**:
- Custom validator без regex: менее читаемый код
- Отдельная функция валидации: нарушение DRY принципа

**Implementation**:
```python
from pydantic import field_validator

class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r'^[А-Яа-яA-Za-z\-]+$', v):
            raise ValueError('Должно содержать только русские/английские буквы и тире')
        return v
```

---

### 3. Валидация сложности пароля

**Decision**: Использовать отдельные Pydantic field_validator для каждого требования

**Rationale**:
- Отдельные валидаторы обеспечивают детальные error messages
- Упрощает тестирование каждого требования независимо
- Читаемый код с понятными именами валидаторов

**Alternatives considered**:
- Один комплексный regex: менее понятные error messages
- Валидация в контроллере: нарушает принцип единственной ответственности

**Implementation**:
```python
class UserCreateRequest(BaseModel):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('Пароль должен содержать минимум 1 заглавную букву')
        if not re.search(r'[a-z]', v):
            raise ValueError('Пароль должен содержать минимум 1 строчную букву')
        if not re.search(r'\d', v):
            raise ValueError('Пароль должен содержать минимум 1 цифру')
        return v
```

---

### 4. Обработка дубликатов email (слоистая архитектура)

**Decision**: Проверка существования email в UsersCrud, уникальный constraint в БД для защиты

**Rationale**:
- **UsersCrud (extends BaseCrud[User])**: содержит методы `find_by_email()` и `email_exists()` - специфичные для User операции
- **UserService**: орхестрация - хеширование пароля, вызов CRUD методов, обработка ошибок
- **Database**: уникальный constraint на email column гарантирует целостность (race condition protection)
- BaseCrud остаётся генериком без специфичной логики

**Слои**:
```
Controller (users.py)
    ↓ валидация request Pydantic schemas
Service (user_service.py)
    ↓ бизнес-логика: хеширование пароля, обработка ошибок
CRUD (users_crud.py extends BaseCrud[User])
    ↓ специфичные операции: find_by_email(), email_exists()
Model (user.py extends BaseDBModel)
    ↓ SQLAlchemy ORM
PostgreSQL (users table)
    ↓ уникальный constraint на email
```

**Alternatives considered**:
- Проверка email в BaseCrud: нарушает принцип генеричности BaseCrud
- Проверка email в UserService: дублирование логики, если другим сервисам нужна проверка email

**Implementation**:
```python
# app/db/crud/users.py
class UsersCrud(BaseCrud[User]):
    async def find_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Найти пользователя по email."""
        return await self.find_one_or_none(db, email=email)

    async def email_exists(self, db: AsyncSession, email: str) -> bool:
        """Проверить существование email."""
        return await self.find_by_email(db, email) is not None

# app/services/user_service.py
class UserService(BaseService):
    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        first_name: str,
        last_name: str,
        password: str
    ) -> User:
        # Проверка существования email через CRUD
        if await self.crud.email_exists(db, email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Пользователь с таким email уже существует'
            )

        # Хеширование пароля
        password_hash = hash_password(password)

        # Создание пользователя
        try:
            return await self.crud.add_one(
                db,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password_hash=password_hash
            )
        except IntegrityError:
            # Race condition protection
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail='Пользователь с таким email уже существует'
            )
```

---

### 5. Асинхронное тестирование с PostgreSQL

**Decision**: Использовать pytest-asyncio с fixtures для асинхронной сессии БД

**Rationale**:
- pytest-asyncio обеспечивает coroutine support
- Fixtures для изоляции тестов (rollback после каждого)
- Faker для генерации реалистичных тестовых данных

**Implementation**:
```python
import pytest
from httpx import AsyncClient
from faker import Faker

@pytest.fixture
async def async_client(db_session: AsyncSession):
    async with AsyncClient(app=app, base_url='http://test') as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_user_success(async_client: AsyncClient, faker: Faker):
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
```

---

## Best Practices

### FastAPI Endpoint Design

- **URL**: `POST /api/v1/users/` (REST collection naming)
- **Success**: status 201 с Location header
- **Conflict**: status 409 для дубликата email
- **Validation Error**: status 422 с детализацией ошибок

### SQLAlchemy 2.0+ Async Patterns

- Использовать `AsyncSession` для асинхронных операций
- Использовать `select()` вместо deprecated `query()`
- `await session.commit()` для транзакций
- `await session.refresh(obj)` для получения сгенерированных ID

### Security

- **bcrypt cost factor**: 12 (default в passlib)
- **Logging**: НЕ логировать пароли (даже захешированные)
- **Response**: Password field не должен возвращаться в API response

---

## Open Questions Resolved

Все неизвестные из Technical Context были разрешены:
- ✅ Язык/версия: Python 3.13
- ✅ Основные зависимости: FastAPI, SQLAlchemy 2.0+, Pydantic V2, Alembic
- ✅ Хранилище: PostgreSQL 17 с AsyncPG
- ✅ Тестирование: pytest, pytest-asyncio, pytest-cov, Faker
- ✅ Целевая платформа: Linux server (Docker)
- ✅ Производительность: 100 req/s, p95 < 500ms
- ✅ Масштаб: один endpoint, одна таблица

---

## References

- [FastAPI User Registration Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [Pydantic V2 Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Passlib bcrypt](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt.html)
