# Data Model: Базовая ролевая модель

**Фича**: 006-base-role-model
**Дата**: 2025-02-07
**Статус**: Утверждён

---

## Обзор

Данный документ описывает модель данных для реализации ролевой модели в системе. Включает новую сущность `Role` и расширение существующей сущности `User`.

---

## Сущность Role

### Назначение
Представляет категорию пользователя с определёнными уровнями разрешений. Справочные данные, создаваемые при инициализации системы.

### Поля

| Имя поля | Тип | Ограничения | Описание |
|----------|-----|-------------|----------|
| `id` | `int` | PRIMARY KEY, AUTOINCREMENT | Уникальный идентификатор роли |
| `name` | `str(100)` | NOT NULL, UNIQUE | Название роли ("user", "manager", "admin") |
| `description` | `str(255)` | NULLABLE | Описание роли (опционально) |
| `created_at` | `datetime` | NOT NULL, DEFAULT NOW() | Время создания записи |
| `updated_at` | `datetime` | NOT NULL, DEFAULT NOW(), ON UPDATE NOW() | Время последнего обновления |

### Constraints

```sql
ALTER TABLE roles ADD CONSTRAINT uq_roles_name UNIQUE (name);
```

### Индексы

- `PRIMARY KEY` на `id` (автоматический)
- `UNIQUE INDEX` на `name` (для быстрого поиска по имени)

### Справочные данные (Seed Data)

| id | name | description |
|----|------|-------------|
| 1 | "user" | "Обычный пользователь системы" |
| 2 | "manager" | "Менеджер с расширенными правами" |
| 3 | "admin" | "Администратор системы" |

---

## Сущность User (изменения)

### Назначение
Представляет пользователя системы. Расширяется добавлением внешнего ключа на роль.

### Новые поля

| Имя поля | Тип | Ограничения | Описание |
|----------|-----|-------------|----------|
| `role_id` | `int` | NOT NULL, FOREIGN KEY → roles(id) | Идентификатор роли пользователя |

### Constraints

```sql
ALTER TABLE users ADD CONSTRAINT fk_users_role_id
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE users MODIFY COLUMN role_id INT NOT NULL;
```

**Обоснование ограничений**:
- `ON DELETE RESTRICT`: Нельзя удалить роль, если на неё ссылаются пользователи
- `ON UPDATE CASCADE`: При изменении id роли (редкий случай) обновить ссылки
- `NOT NULL`: У каждого пользователя должна быть роль

### Индексы

- `INDEX` на `role_id` (для ускорения JOIN операций)

### Изменение existing data

Для существующих пользователей при миграции:
```sql
UPDATE users SET role_id = 1 WHERE role_id IS NULL OR role_id = 0;
```

Все существующие пользователи получают роль "user" (id=1) по умолчанию.

---

## Relationships

### User → Role (Many-to-One)

**SQLAlchemy Definition**:
```python
# app/db/models/user.py
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(BaseDBModel):
    # ...
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"),
        nullable=False,
    )
    role: Mapped["Role"] = relationship(lazy='select')
```

**Lazy Loading**: `lazy='select'` - роль загружается при первом обращении к `user.role`.

**Cascade**: None (explicit). Роль не удаляется при удалении пользователя.

---

## Data Migration Plan

### Migration: `2026_02_07_add_role_model.py`

**Step 1**: Create table `roles`
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Step 2**: Insert seed data (idempotent)
```sql
INSERT INTO roles (id, name, description) VALUES
    (1, 'user', 'Обычный пользователь системы'),
    (2, 'manager', 'Менеджер с расширенными правами'),
    (3, 'admin', 'Администратор системы')
ON CONFLICT (id) DO NOTHING;
```

**Step 3**: Add column `role_id` to `users`
```sql
ALTER TABLE users ADD COLUMN role_id INTEGER;
```

**Step 4**: Create foreign key constraint
```sql
ALTER TABLE users
ADD CONSTRAINT fk_users_role_id
FOREIGN KEY (role_id) REFERENCES roles(id)
ON DELETE RESTRICT ON UPDATE CASCADE;
```

**Step 5**: Set default role for existing users
```sql
UPDATE users SET role_id = 1 WHERE role_id IS NULL;
```

**Step 6**: Make `role_id` NOT NULL
```sql
ALTER TABLE users ALTER COLUMN role_id SET NOT NULL;
```

**Step 7**: Create index on `role_id`
```sql
CREATE INDEX idx_users_role_id ON users(role_id);
```

**Rollback**:
```sql
DROP INDEX IF EXISTS idx_users_role_id;
ALTER TABLE users DROP CONSTRAINT fk_users_role_id;
ALTER TABLE users DROP COLUMN role_id;
DROP TABLE IF EXISTS roles;
```

---

## Validation Rules

### Business Logic Layer (Services)

1. **User Creation**:
   - Если `role_id` не указан при создании пользователя → присвоить роль "user" (id=1)
   - Если `role_id` указан → проверить существование роли

2. **User Update**:
   - Разрешить изменение `role_id` (для администраторов)
   - Проверить существование новой роли

3. **Role Deletion**:
   - Запретить удаление роли, если на неё ссылаются пользователи (обеспечивается на уровне БД через `ON DELETE RESTRICT`)

### API Layer (Schemas)

```python
# app/api/v1/schemas/roles.py
from typing import Literal

class RoleResponse(BaseModel):
    id: int
    name: Literal["user", "manager", "admin"]
    description: str | None = None
```

---

## State Transitions

### Роли пользователей

Роль пользователя может быть изменена администратором:

```
user (1) ←→ manager (2)
  ↑             ↑
  └────→ admin (3)
```

**Правила переходов**:
- Любая роль может быть изменена на любую другую (администратором)
- Сам пользователь не может изменить свою роль
- Пользователь с ролью "admin" может изменить роли других пользователей

---

## Performance Considerations

### Индексы
- `roles.name` (UNIQUE) - для быстрого поиска роли по имени
- `users.role_id` - для ускорения JOIN при проверке роли

### Query Patterns

**Проверка роли при запросе** (тиичный паттерн):
```sql
SELECT u.*, r.*
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE u.id = ?;
```

**Ожидаемое производительность**: <10ms с индексами на 1M записей.

---

## Security Considerations

1. **Role Injection**:
   - Все API endpoints должны проверять роль пользователя
   - Нельзя доверять role_id из JWT payload (проверять из БД)

2. **Privilege Escalation**:
   - Только пользователи с ролью "admin" могут изменять роли других пользователей
   - Пользователь не может изменить свою собственную роль

---

## Summary

| Сущность | Новая/Изменённая | Ключевые поля | Relationships |
|----------|-----------------|---------------|---------------|
| **Role** | Новая | id, name (UNIQUE), description | - |
| **User** | Изменённая | +role_id (FK → roles.id) | User.role → Role (Many-to-One) |

**Следующий шаг**: Создание API контрактов в `contracts/roles.http`.