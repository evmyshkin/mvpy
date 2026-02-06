# Research: Поиск пользователей через API

**Feature**: Поиск пользователей через API
**Date**: 2025-02-06
**Phase**: Phase 0 - Outline & Research

## Research Questions & Decisions

### 1. Какой HTTP метод использовать для поиска пользователей?

**Decision**: GET метод с опциональным query параметром `email`

**Rationale**:
- GET является семантически правильным для операций чтения (поиск не изменяет данные)
- Query параметры позволяют гибко управлять поиском (с email или без)
- RESTful standard для операций поиска/list
- FastAPI автоматически генерирует понятную OpenAPI документацию

**Alternatives considered**:
- POST с телом запроса: менее семантично для операций чтения, не соответствует RESTful практикам
- POST с `/users/search` endpoint: избыточно для простого поиска по одному полю

**Implementation**:
```python
@router.get("/")
async def search_users(email: str | None = None, db: AsyncSession = Depends(connector.get_session())):
    # Логика поиска
```

---

### 2. Как реализовать поиск без учета регистра для email?

**Decision**: Использовать функцию `lower()` или `ilike` в SQLAlchemy

**Rationale**:
- PostgreSQL поддерживает `ilike` (case-insensitive LIKE) нативно
- Альтернатива: `func.lower(User.email) == func.lower(email)`
- Industry standard: email адреса традиционно не чувствительны к регистру
- RFC 5322 определяет local-part как case-sensitive, но на практике почти все системы игнорируют регистр

**Alternatives considered**:
- Хранение email в нижнем регистре: требует миграции данных, может изменить логику существующего кода
- Case-sensitive поиск: противоречит требованию FR-010 и industry practice

**Implementation**:
```python
from sqlalchemy import func

stmt = select(User).where(func.lower(User.email) == func.lower(email))
# или
stmt = select(User).where(User.email.ilike(email))
```

---

### 3. Как исключить пароль из API ответа?

**Decision**: Использовать Pydantic схемы ответа без поля `password_hash`

**Rationale**:
- Существующий паттерн в проекте: `UserCreateResponse` и `UserUpdateResponse` не содержат пароль
- Pydantic автоматически исключает поля, не объявленные в схеме
- Защита чувствительных данных на уровне схемы (defensive programming)
- Совместимо с автоматической генерацией OpenAPI документации

**Alternatives considered**:
- Исключение на уровне SQLAlchemy (`exclude=['password_hash']`): менее явный, может быть забыто
- Исключение на уровне контроллера: требует ручного формирования dict, дублирование кода

**Implementation**:
```python
class UserSearchResponse(BaseModel):
    """Схема ответа при поиске пользователя."""
    id: int
    email: str
    first_name: str
    last_name: str
    # password_hash намеренно отсутствует
```

---

### 4. Нужно ли добавить новый CRUD метод или использовать существующий?

**Decision**: Добавить новый метод `find_all_users` в CRUD, использовать существующий `find_by_email` с модификацией

**Rationale**:
- Существующий `find_by_email` ищет только активных пользователей (`is_active=True`)
- Для поиска всех пользователей нужен отдельный метод
- Для поиска по email без учета регистра нужна модификация существующего метода или новый метод

**Alternatives considered**:
- Использовать только базовый `find_all` из BaseCrud: недостаточно гибко, нельзя фильтровать по email
- Доработать существующий `find_by_email`: риск сломать существующий код (создание пользователя)

**Implementation**:
```python
# Новый метод в UsersCrud
async def find_all_users(self, session: AsyncSession) -> list[User]:
    """Получить список всех пользователей.

    Returns:
        Список всех объектов User
    """
    stmt = select(User)
    result = await session.execute(stmt)
    return list(result.scalars().all())

# Модифицированный метод для case-insensitive поиска
async def find_by_email_case_insensitive(self, session: AsyncSession, email: str) -> User | None:
    """Найти пользователя по email без учета регистра.

    Args:
        session: Асинхронная сессия БД
        email: Email пользователя

    Returns:
        Объект User или None если не найден
    """
    stmt = select(User).where(func.lower(User.email) == func.lower(email))
    result = await session.execute(stmt)
    return result.scalars().first()
```

---

### 5. Как обрабатывать пустой список пользователей?

**Decision**: Возвращать пустой массив с HTTP 200

**Rationale**:
- RESTful standard: пустой результат ≠ ошибка
- 404 используется когда конкретный ресурс не найден (поиск по email)
- Consistent behavior: GET /api/v1/users/ возвращает array (пустой или с элементами)

**Alternatives considered**:
- Возвращать 404 для пустого списка: не соответствует RESTful практике, путает клиента
- Возвращать 204 No Content: семантически неверный (content есть, просто пустой)

**Implementation**:
```python
users = await user_service.get_all_users(session=db)
return users  # Пустой список автоматически конвертируется в JSON []
```

---

### 6. Нужно ли валидировать email в query параметре?

**Decision**: Использовать Pydantic `EmailStr` для автоматической валидации

**Rationale**:
- FastAPI автоматически валидирует query параметры через Pydantic
- `EmailStr` проверяет формат email согласно RFC 5322
- Автоматический возврат 422 с описанием ошибки при невалидном формате
- Переиспользование существующей валидации из проекта

**Alternatives considered**:
- Ручная валидация в контроллере: дублирование кода, нарушение DRY
- Использование regex: сложнее поддерживать, Pydantic уже делает это

**Implementation**:
```python
from pydantic import EmailStr

@router.get("/")
async def search_users(
    email: EmailStr | None = None,  # Автовалидация FastAPI
    db: AsyncSession = Depends(connector.get_session())
):
    # email уже валидирован или None
```

---

### 7. Какие сообщения об ошибках возвращать?

**Decision**: Использовать локализованные сообщения на русском языке

**Rationale**:
- Требование FR-011 и конституции (Принцип XI)
- Pydantic позволяет кастомизировать сообщения валидации
- HTTPException с понятным `detail` на русском

**Alternatives considered**:
- Сообщения на английском: противоречит требованиям
- Коды ошибок без текста: менее понятно для администраторов

**Implementation**:
```python
# Для 404 (пользователь не найден)
raise HTTPException(
    status_code=HTTP_404_NOT_FOUND,
    detail='Пользователь с указанным email не найден'
)

# Для 422 (невалидный email) - автоматическая валидация Pydantic
# Можно кастомизировать через EmailStr настройки
```

---

## Best Practices Research

### SQLAlchemy 2.0+ Performance

- **Use `select()` instead of `query()`**: Конституция (Принцип XIV) требует использования `select()`
- **Use `scalars().first()` for single result**: Более эффективно чем `one_or_none()` для опциональных результатов
- **Use `scalars().all()` for lists**: Возвращает список объектов вместо Row объектов

### FastAPI Query Parameters

- **Optional query params**: `email: str | None = None` позволяет параметр быть пропущенным
- **Automatic validation**: FastAPI валидирует типы через Pydantic
- **OpenAPI documentation**: Автоматически генерируется для query параметров

### Pydantic V2 Patterns

- **Response models**: Использовать `response_model` в декораторе endpoint для автоматической валидации ответов
- **Exclusion**: Поля не указанные в схеме автоматически исключаются из ответа
- **Annotated types**: Использовать `Annotated[type, Field(...)]` для сложной валидации

## Technology Stack Confirmation

✅ **Confirmed**:
- Python 3.13
- FastAPI
- SQLAlchemy 2.0+ с AsyncPG драйвером
- Pydantic V2 с EmailStr
- PostgreSQL 17
- pytest-asyncio для тестов

## Dependencies & Integration Points

1. **Existing model User**: Используется без изменений
2. **Existing UsersCrud**: Добавляются новые методы `find_all_users` и `find_by_email_case_insensitive`
3. **Existing UserService**: Добавляются методы для оркестрации поиска
4. **Existing schemas**: Добавляются `UserSearchResponse` (для одного пользователя) и `UserListResponse` (для списка)
5. **Existing controller users.py**: Добавляется GET `/` endpoint

## Unresolved Questions

Нет нерешенных вопросов. Все технические решения приняты.