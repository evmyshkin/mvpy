# Data Model: Поиск пользователей через API

**Feature**: Поиск пользователей через API
**Date**: 2025-02-06
**Phase**: Phase 1 - Design & Contracts

## Entities

### User (Сущность пользователя)

**Описание**: Пользователь системы. Используется существующая модель без изменений.

**Атрибуты**:

| Поле | Тип | Описание | Валидация | Nullable |
|------|-----|----------|-----------|----------|
| `id` | int | Уникальный идентификатор | PK, auto-increment | Нет |
| `email` | str(255) | Email адрес | Уникальный, RFC 5322 | Нет |
| `first_name` | str(100) | Имя пользователя | Русские/английские буквы и дефис | Нет |
| `last_name` | str(100) | Фамилия пользователя | Русские/английские буквы и дефис | Нет |
| `password_hash` | str | Хеш пароля (bcrypt) | - | Нет |
| `is_active` | bool | Флаг активности | - | Нет |
| `created_at` | datetime | Дата создания | - | Нет |
| `updated_at` | datetime | Дата обновления | - | Нет |

**Примечания**:
- `password_hash` **НЕ ВОЗВРАЩАЕТСЯ** в API ответах (требование безопасности)
- Поиск по email выполняется без учета регистра (case-insensitive)
- Модель `User` уже существует в БД, миграции не требуются

## Pydantic Схемы

### Запросные схемы (Request Schemas)

#### UserSearchQuery

**Описание**: Параметры запроса для поиска пользователей

**Поля**:

| Поле | Тип | Обязательный | По умолчанию | Описание |
|------|-----|--------------|--------------|----------|
| `email` | EmailStr | Нет | None | Email для поиска конкретного пользователя |

**Валидация**:
- Если `email` указан: валидация формата через Pydantic `EmailStr`
- Если `email` не указан: возвращаются все пользователи

### Ответные схемы (Response Schemas)

#### UserSearchResponse

**Описание**: Данные одного пользователя для ответа API

**Поля**:

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | int | Уникальный идентификатор пользователя |
| `email` | str | Email адрес пользователя |
| `first_name` | str | Имя пользователя |
| `last_name` | str | Фамилия пользователя |

**Важно**: Поле `password_hash` намеренно отсутствует для безопасности

#### UserListResponse

**Описание**: Список пользователей для ответа API

**Поля**:

```python
# Вариант 1: Прямой список
type: list[UserSearchResponse]

# Вариант 2: Обертка с метаданными
users: list[UserSearchResponse]
total: int  # Общее количество
```

**Решение**: Использовать Вариант 1 (прямой список) для соответствия требованию scoped-разработки (Принцип X)
- Метаданные (total, pagination) не требуются в текущей версии
- Упрощает API и реализацию

## Отношения (Relationships)

### User

**Отношения**: Нет внешних ключей в текущей версии

**Примечание**: В будущих версиях могут быть добавлены связи с:
- Orders (заказы пользователя)
- Roles (роли пользователя)
- Permissions (права доступа)

## Валидационные правила

### Email валидация

**Формат**: RFC 5322 (стандартный email формат)

**Реализация**: Pydantic `EmailStr` - автоматическая валидация

**Примеры валидных email**:
- `user@example.com`
- `user.name@example.com`
- `user+tag@example.com`

**Примеры невалидных email**:
- `user@` (отсутствует домен)
- `@example.com` (отсутствует local-part)
- `user example.com` (отсутствует @)

**HTTP статус**: 422 Unprocessable Entity при невалидном формате

### Поиск без учета регистра

**Правило**: Email поиск не чувствителен к регистру

**Примеры**:
- `Test@Example.com` = `test@example.com` = `TEST@EXAMPLE.COM`

**Реализация**: SQLAlchemy `func.lower()` или `ilike`

## Состояния и переходы (State Transitions)

**Не применимо**: Сущность User не изменяет состояние в рамках этой фичи (только чтение)

## Безопасность данных

### Полевая безопасность (Field-Level Security)

**Пароль**:
- **Хранение**: `password_hash` (bcrypt 4.0.1)
- **API ответ**: Никогда не возвращается
- **БД запрос**: Выбирается модель User, но Pydantic схема исключает поле из ответа

**Реализация**:
```python
# Pydantic схема автоматически исключает password_hash
class UserSearchResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    # password_hash отсутствует
```

## Индексы и производительность

### Существующие индексы

**Email индекс**: PostgreSQL автоматически создает индекс для `UNIQUE` ограничения

```sql
-- Автоматический индекс для email (уникальное ограничение)
CREATE UNIQUE INDEX ix_users_email ON users(email);
```

**Производительность**:
- Поиск по email: O(log n) - B-tree индекс
- Получение всех пользователей: O(n) - full table scan

**Примечание**: Для 10,000 пользователей производительность достаточна (требование SC-004: <2 секунды)

## CRUD операции

### Методы CRUD слоя

1. **find_by_email_case_insensitive(session, email) -> User | None**
   - Поиск пользователя по email без учета регистра
   - Возвращает None если не найден
   - SQL: `SELECT * FROM users WHERE LOWER(email) = LOWER(:email) LIMIT 1`

2. **find_all_users(session) -> list[User]**
   - Получение списка всех пользователей
   - Возвращает пустой список если пользователей нет
   - SQL: `SELECT * FROM users`

### Методы Service слоя

1. **search_user_by_email(session, UserSearchQuery) -> UserSearchResponse**
   - Поиск пользователя по email
   - Преобразует User модель в UserSearchResponse
   - Генерирует HTTPException 404 если не найден

2. **get_all_users(session) -> list[UserSearchResponse]**
   - Получение списка всех пользователей
   - Преобразует список User моделей в list[UserSearchResponse]

## Миграции БД

**Статус**: Миграции не требуются

**Обоснование**:
- Модель User уже существует
- Новые CRUD методы не изменяют структуру БД
- Новые Pydantic схемы не влияют на БД

## Тестовые данные

### Фикстуры для тестов

**valid_user_search_result**: UserSearchResponse
```python
{
    "id": 1,
    "email": "test@example.com",
    "first_name": "Иван",
    "last_name": "Иванов"
}
```

**multiple_users_list**: list[UserSearchResponse]
```python
[
    {"id": 1, "email": "user1@example.com", "first_name": "Иван", "last_name": "Иванов"},
    {"id": 2, "email": "user2@example.com", "first_name": "Петр", "last_name": "Петров"},
    {"id": 3, "email": "user3@example.com", "first_name": "Сидор", "last_name": "Сидоров"}
]
```

**empty_user_list**: list[UserSearchResponse]
```python
[]
```