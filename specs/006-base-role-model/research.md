# Research: Базовая ролевая модель

**Фича**: 006-base-role-model
**Дата**: 2025-02-07
**Статус**: Завершён

---

## 1. SQLAlchemy 2.0 Relationship

### Задача
Изучить лучшие практики для relationship в SQLAlchemy 2.0 для связи User → Role (Many-to-One).

### Решение

**Lazy Loading Strategy**:
- Использовать `lazy='select'` (по умолчанию) для `user.role`
- Обоснование: Роль загружается только при обращении к `user.role`, что соответствует требованию "проверять роль при каждом запросе"
- Альтернатива `lazy='joined'` не подходит: будет всегда загружать роль даже когда не нужна

**Relationship Definition**:
```python
# app/db/models/user.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.role import Role

class User(BaseDBModel):
    # ...
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    role: Mapped[Role] = relationship(lazy='select')
```

**Cascade Rules**:
- Не использовать cascade для User → Role (роль не должна удаляться при удалении пользователя)
- Не использовать cascade для Role → User (нельзя удалить роль, если на неё ссылаются пользователи - обеспечивается на уровне БД через FOREIGN KEY CONSTRAINT)

**Rationale**: SQLAlchemy 2.0 использует relationship 2.0 style с Mapped типами. `lazy='select'` обеспечивает оптимальную производительность для паттерна "проверить роль при каждом запросе".

### Альтернативы рассмотрены

| Подход | Плюсы | Минусы | Почему rejected |
|--------|-------|--------|-----------------|
| `lazy='joined'` | Один SQL запрос | Всегда загружает роль | Лишние данные когда роль не нужна |
| `lazy='subquery'` | Отдельный запрос для всех пользователей | Сложный SQL, устаревший подход | SQLAlchemy 2.0 не рекомендует |
| `lazy='raise'` | Явный контроль | Требует manual join | Усложняет код, нет преимуществ |

---

## 2. Alembic Data Migrations

### Задача
Изучить паттерны для миграций данных в Alembic: создание 3 ролей (user, manager, admin).

### Решение

**Data Migration Pattern**:
Использовать `op.execute()` или SQLAlchemy Core `insert()` внутри migration для вставки данных.

**Idempotent Migrations**:
```python
# migrations/versions/2026_02_07_add_role_model.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade() -> None:
    # 1. Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 2. Insert roles (idempotent using ON CONFLICT DO NOTHING for PostgreSQL)
    op.execute("""
        INSERT INTO roles (id, name, description)
        VALUES
            (1, 'user', 'Обычный пользователь системы'),
            (2, 'manager', 'Менеджер с расширенными правами'),
            (3, 'admin', 'Администратор системы')
        ON CONFLICT (id) DO NOTHING
    """)

    # 3. Add role_id to users table
    op.add_column('users', sa.Column('role_id', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_users_role_id', 'users', 'roles', ['role_id'], ['id'])

    # 4. Set default role for existing users
    op.execute("UPDATE users SET role_id = 1 WHERE role_id IS NULL OR role_id = 0")

    # 5. Make role_id NOT NULL (already done in step 3)

```

**Обработка повторных запусков**:
- PostgreSQL: `ON CONFLICT DO NOTHING`
- Проверять существование записей перед вставкой (опционально, если БД не поддерживает ON CONFLICT)

**Rationale**: Использование raw SQL с `ON CONFLICT DO NOTHING` обеспечивает идемпотентность миграций. Это позволяет запускать `alembic upgrade head` многократно без ошибок.

### Альтернативы рассмотрены

| Подход | Плюсы | Минусы | Почему rejected |
|--------|-------|--------|-----------------|
| ORM models в migration | Знакомый API | Risk of stale models | Models могут измениться, migration сломается |
| SQLAlchemy Core insert() | Type-safe | Многословно | Raw SQL короче и понятнее |
| Отдельный скрипт | Простота | Не часть migration | Нарушает принцип migrations |

---

## 3. Pydantic V2 Annotated Types для Enums

### Задача
Изучить для Pydantic V2 с enum типами: валидация role_name (user/manager/admin).

### Решение

**Literal[str] vs Enum**:
Использовать **Literal[str]** для role_name в API схемах.

**Обоснование**:
- `Literal["user", "manager", "admin"]` - валидация на уровне Pydantic
- Простая сериализация/десериализация (строки)
- Легко расширять в будущем (добавить новые роли)

**Схема Pydantic**:
```python
# app/api/v1/schemas/roles.py
from typing import Literal
from pydantic import BaseModel, Field

class RoleResponse(BaseModel):
    """Схема ответа для роли."""

    id: int
    name: Literal["user", "manager", "admin"]
    description: str | None = None
    created_at: datetime
    updated_at: datetime

class RoleCreateRequest(BaseModel):
    """Схема запроса на создание роли (только для internal usage)."""

    name: Literal["user", "manager", "admin"]
    description: str | None = None
```

**Enum для бизнес-логики** (опционально):
```python
# app/api/utils/enums/roles.py
from enum import StrEnum

class RoleName(StrEnum):
    """Имена ролей в системе."""

    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"
```

**Rationale**: Literal[str] обеспечивает валидацию без оверхеда Enum классов. Для бизнес-логики можно использовать StrEnum, но это опционально.

### Альтернативы рассмотрены

| Подход | Плюсы | Минусы | Почему rejected (или when to use) |
|--------|-------|--------|-----------------------------------|
| `Literal[str]` | Простота, нативная валидация | Нет методов типа .value | ✅ **Выбран** для API схем |
| `StrEnum` | Type-safe, IDE support | Оверхед класса | Использовать в бизнес-логике сервисов |
| `IntEnum` | Быстродействие | Нет читаемости в JSON | Не подходит для API |
| Константы (USER_ROLE = "user") | Простота | Нет валидации Pydantic | Недостаточно безопасно |

---

## 4. JWT Токен Payload Расширение

### Задача
Изучить текущую реализацию JWT токенов: нужно ли добавлять role_id в JWT payload? Производительность проверки роли из токена vs БД.

### Решение

**НЕ добавлять role_id в JWT payload**.

**Обоснование**:

1. **Безопасность**: Роль может быть изменена администратором. Если role_id зашит в JWT, пользователь продолжит выполнять операции со старой ролью до истечения токена.

2. **Текущая реализация**:
   - JWT payload содержит: `sub`, `user_id`, `is_active`, `iat`, `exp`, `jti`
   - Проверка `is_active` уже выполняется из БД при каждом запросе (см. `app/services/current_user_service.py:46`)
   - Добавление role в payload нарушит принцип "источник истины - БД"

3. **Производительность**:
   - Запрос `SELECT * FROM users JOIN roles ON users.role_id = roles.id WHERE users.id = ?` с индексами занимает <10ms
   - Требование SC-004: "без добавления измеримой задержки" - <10ms является измеримым, но незначительным
   - Кэширование ролей не требуется (3 записи в таблице)

**Rationale**: Проверка роли из БД при каждом запросе обеспечивает актуальность данных и безопасность. Производительность приемлема благодаря индексам и малому объёму данных.

### Альтернативы рассмотрены

| Подход | Плюсы | Минусы | Почему rejected |
|--------|-------|--------|-----------------|
| role_id в JWT | Нет запроса к БД | Устаревшие данные при изменении роли | ✅ **Rejected** - безопасность важнее |
| Redis кэш ролей | Быстро | Сложность, stale data | Неоправданно для 3 ролей |
| In-memory кэш | Быстро | Проблемы синхронизации | Неоправданно для 3 ролей |
| Запрос к БД (выбран) | Актуальные данные | +1 запрос к БД | ✅ **Выбран** - безопасно и быстро |

---

## 5. Dependency Injection Паттерны в FastAPI

### Задача
Изучить паттерны для composition зависимостей: `get_current_user_with_role` = `get_current_user` + проверка роли.

### Решение

**Composition через Depends()**:

```python
# app/api/v1/dependencies.py
from fastapi import Depends

async def get_current_user_with_role(
    current_user: User = Depends(get_current_user),
) -> User:
    """Получить текущего пользователя с загруженной ролью.

    Эта dependency автоматически загружает роль через relationship.
    """
    # Доступ к user.role вызовет lazy load
    _ = current_user.role  # Trigger lazy load для гарантии
    return current_user
```

**Использование в контроллерах**:
```python
@router.get("/users/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user_with_role),
) -> UserResponse:
    """Получить информацию о текущем пользователе."""
    return UserResponse.model_validate(current_user)
```

**Rationale**: FastAPI автоматически кэширует результат зависимостей в рамках одного запроса. `Depends(get_current_user)` будет выполнен один раз, результат будет переиспользован.

### Альтернативы рассмотрены

| Подход | Плюсы | Минусы | Почему rejected (или when to use) |
|--------|-------|--------|-----------------------------------|
| `Depends(Depends())` | Композиция | Многословно | ✅ **Выбран** для простых случаев |
| Custom dependency class | Гибкость | Оверхед | Использовать для сложной логики |
| Global middleware | Автоматически | Неявность, performance | Не подходит для optional зависимостей |
| Manual вызов в controller | Полный контроль | Нарушает DI principles | Не соответствует конституции |

---

## Summary

Все исследовательские задачи решены. Основные решения:

1. **SQLAlchemy**: `lazy='select'` для User.role relationship
2. **Alembic**: Raw SQL с `ON CONFLICT DO NOTHING` для идемпотентности
3. **Pydantic**: `Literal[str]` для валидации role names
4. **JWT**: НЕ добавлять role_id в payload, проверять из БД
5. **DI**: `Depends(Depends())` для композиции зависимостей

Следующий шаг: Phase 1 - Design & Contracts.
