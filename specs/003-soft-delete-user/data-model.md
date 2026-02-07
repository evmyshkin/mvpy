# Data Model: Деактивация пользователя

**Фича**: 003-soft-delete-user
**Дата**: 2026-02-06
**Статус**: Phase 1 - Design

---

## Обзор

Добавление поля `is_active` в модель `User` для управления активностью пользователей. Деактивация помечает пользователя как неактивного без физического удаления данных из базы данных.

---

## Сущность: User

### Назначение
Представляет пользователя системы с возможностью деактивации.

### Поля

| Поле | Тип | Nullable | Default | Описание |
|------|-----|----------|---------|----------|
| `id` | Integer | NO | autoincrement | Уникальный идентификатор (унаследовано от BaseDBModel) |
| `email` | String(255) | NO | - | Уникальный email пользователя |
| `first_name` | String(100) | NO | - | Имя пользователя |
| `last_name` | String(100) | NO | - | Фамилия пользователя |
| `password_hash` | String | NO | - | Хеш пароля (bcrypt) |
| `created_at` | DateTime(timezone=True) | NO | now() | Время создания записи |
| `updated_at` | DateTime(timezone=True) | NO | now() | Время последнего обновления |
| `is_active` | **Boolean** | NO | **true** | **Флаг активности пользователя (НОВОЕ)** |

### Описание поля `is_active`

- **Тип**: `Boolean`
- **Nullable**: `NO`
- **Default**: `True` (новые пользователи активны по умолчанию)
- **Server default**: `true` (для существующих записей при миграции)
- **Назначение**: Управление активностью пользователя
  - `True` - пользователь активен, может аутентифицироваться и обновляться
  - `False` - пользователь деактивирован, не может аутентифицироваться или обновляться

---

## Миграция базы данных

### Изменения в таблице `users`

```sql
-- Alembic migration
ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT true;
```

### Обратная миграция (downgrade)

```sql
ALTER TABLE users DROP COLUMN is_active;
```

### Влияние на существующие данные

- Все существующие пользователи автоматически получат `is_active=True` при миграции
- Не требуются дополнительные миграции данных
- Миграция безопасна и обратима

---

## ORM Модель (SQLAlchemy 2.0+)

### Определение в `app/db/models/user.py`

```python
"""Модель пользователя."""

from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.db.base import BaseDBModel


class User(BaseDBModel):
    """Модель пользователя."""

    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default='true',
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

---

## CRUD Операции

### Изменения в `app/db/crud/users.py`

#### Метод `find_by_email`

**Обновление**: Добавить фильтрацию по `is_active=True`

```python
async def find_by_email(self, session: AsyncSession, email: str) -> User | None:
    """Найти активного пользователя по email.

    Деактивированные пользователи (is_active=False) исключаются из поиска.

    Args:
        session: Асинхронная сессия БД
        email: Email пользователя

    Returns:
        Объект User или None если не найден или пользователь деактивирован
    """
    stmt = select(User).where(
        and_(
            User.email == email,
            User.is_active == True,  # Фильтрация активных пользователей
        )
    )
    result = await session.execute(stmt)
    return result.scalars().first()
```

#### Новый метод `deactivate_by_email`

```python
async def deactivate_by_email(self, session: AsyncSession, email: str) -> User | None:
    """Деактивировать пользователя по email.

    Args:
        session: Асинхронная сессия БД
        email: Email пользователя для деактивации

    Returns:
        Объект User с is_active=False или None если не найден
    """
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if user is not None:
        user.is_active = False
        # updated_at автоматически обновится через onupdate=func.now()

    return user
```

---

## Валидация

### Ограничения

- `is_active` не может быть `NULL` (NOT NULL constraint)
- Допустимые значения: `true` или `false`
- При создании пользователя по умолчанию устанавливается `true`

### Бизнес-логика

- Активный пользователь (`is_active=True`):
  - Может аутентифицироваться
  - Может быть обновлён через PATCH
  - Может быть найден через GET и поиск по email

- Деактивированный пользователь (`is_active=False`):
  - **НЕ** может аутентифицироваться
  - **НЕ** может быть обновлён через PATCH (возвращает 404)
  - **НЕ** может быть найден через поиск по email (returns None)
  - Данные сохраняются в БД для compliance

---

## SQL Примеры

### Создание активного пользователя

```sql
INSERT INTO users (email, first_name, last_name, password_hash, is_active)
VALUES ('user@example.com', 'Иван', 'Иванов', 'hash123', true);
```

### Деактивация пользователя

```sql
UPDATE users SET is_active = false WHERE email = 'user@example.com';
```

### Поиск активного пользователя

```sql
SELECT * FROM users WHERE email = 'user@example.com' AND is_active = true;
```

### Попытка найти деактивированного пользователя

```sql
SELECT * FROM users WHERE email = 'user@example.com' AND is_active = true;
-- Returns: 0 rows (даже если пользователь существует с is_active=false)
```

---

## Производительность

### Индексы

Рекомендуется добавить индекс на `is_active` для оптимизации фильтрации (будет добавлено в отдельной задаче при необходимости):

```sql
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = false;
```

Примечание: Частичный индекс (WHERE is_active = false) оптимизирует поиск деактивированных пользователей, если такая функциональность потребуется в будущем.

---

## Следующие шаги

1. ✅ Модель данных определена
2. ➡️ Создать API контракты (`contracts/openapi.yaml`)
4. ➡️ Обновить agent context

---

**Статус**: ✅ Data model разработан, готов к имплементации
