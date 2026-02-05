# Data Model: Создание пользователя через API

**Feature**: 001-create-user | **Date**: 2026-02-05

## Entity: User

### Описание

Сущность пользователя системы. Пользователь идентифицируется по уникальному email адресу (поле username отсутствует). Пароль хранится в захешированном виде с использованием bcrypt.

### Поля

| Поле | Тип | Обязательное | Уникальное | Описание | Валидация |
|------|-----|--------------|------------|----------|-----------|
| `id` | UUID/Integer | Да | Да | Первичный ключ | Автогенерация |
| `email` | String(255) | Да | Да | Email адрес пользователя | RFC 5322 формат |
| `first_name` | String(100) | Да | Нет | Имя пользователя | Только русские/английские буквы и тире |
| `last_name` | String(100) | Да | Нет | Фамилия пользователя | Только русские/английские буквы и тире |
| `password_hash` | String | Да | Нет | Захешированный пароль | bcrypt hash |
| `created_at` | DateTime | Да | Нет | Время создания | Автогенерация |
| `updated_at` | DateTime | Да | Нет | Время обновления | Автогенерация |

### Relationships

Нет внешних связей (first version).

### Constraints

```sql
-- Уникальный constraint на email
ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email);

-- Not null constraints
ALTER TABLE users MODIFY COLUMN email VARCHAR(255) NOT NULL;
ALTER TABLE users MODIFY COLUMN first_name VARCHAR(100) NOT NULL;
ALTER TABLE users MODIFY COLUMN last_name VARCHAR(100) NOT NULL;
ALTER TABLE users MODIFY COLUMN password_hash TEXT NOT NULL;
```

### Validation Rules

**Email**:
- Формат: RFC 5322 (упрощённая проверка)
- Длина: до 255 символов
- Уникален: да

**First Name**:
- Длина: до 100 символов
- Формат: только русские (А-Яа-я) и английские (A-Za-z) буквы и тире (-)
- Regex: `^[А-Яа-яA-Za-z\-]+$`
- Примеры валидных: "Иван", "John", "Мария-Изабелла"
- Примеры невалидных: "Иван1", "John_Doe", "Анна&Петр"

**Last Name**:
- Те же правила что и First Name
- Примеры валидных: "Иванов", "Smith", "Салтыков-Щедрин"
- Примеры невалидных: "Иванов1", "Smith_Jones", "Петров*"

**Password**:
- Минимальная длина: 8 символов
- Максимальная длина: 100 символов
- Обязательные требования:
  - Минимум 1 заглавная буква (A-Z)
  - Минимум 1 строчная буква (a-z)
  - Минимум 1 цифра (0-9)
- Примеры валидных: "Password123", "MyPass1", "Secure456"
- Примеры невалидных: "password", "PASSWORD", "Pass1", "Пароль123"

### State Transitions

Нет переходов состояний (простая CRUD операция создания).

### SQLAlchemy Model

```python
# app/db/models/user.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseDBModel


class User(BaseDBModel):
    """Модель пользователя."""

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
```

```python
# app/db/models/__init__.py
from app.db.models.user import User

__all__ = ['User']
```

### Alembic Migration

```python
# migrations/versions/[timestamp]_create_users_table.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='users_email_unique')
    )


def downgrade():
    op.drop_table('users')
```

---

## Pydantic Schemas

### Request Schema

```python
# app/api/v1/schemas/users.py
from pydantic import BaseModel, EmailStr, field_validator
import re


class UserCreateRequest(BaseModel):
    """Схема запроса на создание пользователя."""

    email: EmailStr
    first_name: str
    last_name: str
    password: str

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Валидация имени/фамилии."""
        if not re.match(r'^[А-Яа-яA-Za-z\-]+$', v):
            raise ValueError(
                'Должно содержать только русские/английские буквы и тире'
            )
        if len(v) > 100:
            raise ValueError('Длина не должна превышать 100 символов')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """Валидация длины пароля."""
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        if len(v) > 100:
            raise ValueError('Пароль не должен превышать 100 символов')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Валидация сложности пароля."""
        if not re.search(r'[A-Z]', v):
            raise ValueError(
                'Пароль должен содержать минимум 1 заглавную букву'
            )
        if not re.search(r'[a-z]', v):
            raise ValueError(
                'Пароль должен содержать минимум 1 строчную букву'
            )
        if not re.search(r'\d', v):
            raise ValueError('Пароль должен содержать минимум 1 цифру')
        return v
```

### Response Schema

```python
# app/api/v1/schemas/users.py
from pydantic import BaseModel, ConfigDict


class UserCreateResponse(BaseModel):
    """Схема ответа при создании пользователя."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str
    last_name: str
    created_at: str
    updated_at: str
```

---

## Data Flow

```
Client Request (JSON)
    ↓
Pydantic Validation (UserCreateRequest)
    ↓
Controller (users.py)
    ↓
Service (user_service.py)
    ├── UsersCrud.email_exists()
    ├── hash_password()
    └── UsersCrud.add_one()
        ↓
Database (PostgreSQL)
    ├── Unique Constraint (email)
    └── Insert
        ↓
User Entity
    ↓
Pydantic Serialization (UserCreateResponse)
    ↓
Client Response (JSON, status 201)
```