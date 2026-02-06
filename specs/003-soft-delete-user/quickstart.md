# Quickstart Guide: Деактивация пользователя

**Фича**: 003-soft-delete-user
**Дата**: 2026-02-06
**Для разработчиков**: Инструкция по работе с функциональностью деактивации

---

## Обзор функциональности

Деактивация пользователя позволяет временно запретить доступ в систему без удаления данных. Это отличается от физического удаления тем, что:
- Все данные пользователя сохраняются в базе данных
- Пользователь не может аутентифицироваться
- Пользователь не может быть обновлён через API
- Повторная деактивация возвращает 404 (как если пользователя не существует)

---

## Шаг 1: Применение миграции базы данных

### Создание миграции

```bash
alembic revision -m "add is_active field to users"
```

### Содержимое миграции

Файл: `migrations/versions/XXXX_add_is_active_field_to_users.py`

```python
"""add is_active field to users

Revision ID: XXXXXXXXXXXX
Revises: YYYYYYYYYYYYY
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'XXXXXXXXXXXXXX'
down_revision: Union[str, None] = 'YYYYYYYYYYYYY'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавить поле is_active в таблицу users."""
    op.add_column(
        'users',
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default='true',
        ),
    )


def downgrade() -> None:
    """Удалить поле is_active из таблицы users."""
    op.drop_column('users', 'is_active')
```

### Применение миграции

```bash
# Для локальной разработки
alembic upgrade head

# Для production (через Docker Compose)
docker-compose exec web alembic upgrade head
```

### Проверка

```bash
# Проверить что колонка создана
docker-compose exec db psql -U postgres -d mvpy -c "\d users"

# Ожидаемый вывод:
# ...
# is_active | boolean | not null true | ...
```

---

## Шаг 2: Обновление модели User

### Файл: `app/db/models/user.py`

Добавить поле `is_active` в модель:

```python
from sqlalchemy import Boolean

# ... существующие импорты

class User(BaseDBModel):
    """Модель пользователя."""

    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    # НОВОЕ ПОЛЕ
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

## Шаг 3: Обновление CRUD операций

### Файл: `app/db/crud/users.py`

Обновить метод `find_by_email` для фильтрации активных пользователей:

```python
from sqlalchemy import select, and_

# ... существующий код

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
            User.is_active,  # Фильтрация активных пользователей
        )
    )
    result = await session.execute(stmt)
    return result.scalars().first()


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
        await session.commit()

    return user
```

---

## Шаг 4: Добавление метода в UserService

### Файл: `app/services/user_service.py`

```python
from starlette.status import HTTP_404_NOT_FOUND

# ... существующие импорты

class UserService(BaseService):
    """Сервис для бизнес-логики пользователей."""

    def __init__(self) -> None:
        super().__init__()
        self.crud = UsersCrud()

    # ... существующие методы (create_user, update_user)

    async def deactivate_user(
        self,
        session: AsyncSession,
        email: str,
    ) -> None:
        """Деактивировать пользователя по email.

        Args:
            session: Асинхронная сессия БД
            email: Email пользователя для деактивации

        Raises:
            HTTPException(404): Если пользователь не найден или уже деактивирован
        """
        user = await self.crud.find_by_email(session, email)
        if user is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=ErrorMessages.USER_NOT_FOUND.value,
            )

        await self.crud.deactivate_by_email(session, email)
```

---

## Шаг 5: Добавление DELETE эндпоинта

### Файл: `app/api/v1/controllers/users.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import connector
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])
user_service = UserService()

# ... существующие эндпоинты (POST, PATCH, GET)


@router.delete("/{email}")
async def deactivate_user(
    email: str,
    session: AsyncSession = Depends(connector.get_session),
) -> None:
    """Деактивировать пользователя по email.

    Args:
        email: Email пользователя для деактивации
        session: Асинхронная сессия БД

    Returns:
        204 No Content при успешной деактивации

    Raises:
        HTTPException(404): Если пользователь не найден или уже деактивирован
        HTTPException(400): Если email имеет некорректный формат
    """
    await user_service.deactivate_user(session=session, email=email)
    return Response(status_code=HTTP_204_NO_CONTENT)
```

---

## Шаг 6: Тестирование API

### Примеры запросов

#### Успешная деактивация

```bash
curl -X DELETE http://localhost:8000/api/v1/users/user@example.com \
  -H "Content-Type: application/json"

# Ожидаемый ответ: 204 No Content (пустое тело)
```

#### Пользователь не найден

```bash
curl -X DELETE http://localhost:8000/api/v1/users/nonexistent@example.com

# Ожидаемый ответ:
# {
#   "detail": "Пользователь не найден"
# }
# Статус: 404 Not Found
```

#### Повторная деактивация

```bash
# Первая деактивация
curl -X DELETE http://localhost:8000/api/v1/users/user@example.com
# Ответ: 204 No Content

# Повторная деактивация
curl -X DELETE http://localhost:8000/api/v1/users/user@example.com
# Ответ: 404 Not Found (пользователь уже деактивирован)
```

---

## Проверка через SQL

### Проверка состояния пользователя

```sql
-- Посмотреть статус пользователя
SELECT email, first_name, last_name, is_active, created_at, updated_at
FROM users
WHERE email = 'user@example.com';
```

### Поиск активных пользователей

```sql
-- Найти только активных пользователей
SELECT * FROM users WHERE is_active = true;
```

### Поиск деактивированных пользователей

```sql
-- Найти деактивированных пользователей (для админских целей)
SELECT * FROM users WHERE is_active = false;
```

---

## Поведение системы

### Что происходит при деактивации

1. **Устанавливается** `is_active=False` в базе данных
2. **Обновляется** поле `updated_at` автоматически
3. **Все данные** пользователя сохраняются (email, имя, пароль и т.д.)
4. **API возвращает** 204 No Content

### Что НЕ работает для деактивированного пользователя

- ❌ Аутентификация (вход в систему)
- ❌ Обновление через PATCH `/api/v1/users/{id}`
- ❌ Поиск через `find_by_email()` (возвращает `None`)
- ❌ Повторная деактивация (возвращает 404)

### Что СОХРАНЯЕТСЯ

- ✅ Все данные пользователя в базе данных
- ✅ История создания и обновлений (`created_at`, `updated_at`)
- ✅ Связи с другими сущностями (если есть)

---

## Отладка

### Локальное тестирование

```bash
# Запустить сервер
uv run uvicorn app.main:app --reload

# В другом терминале: создать пользователя
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Тест",
    "last_name": "Тестов",
    "password": "Password123"
  }'

# Деактивировать пользователя
curl -X DELETE http://localhost:8000/api/v1/users/test@example.com

# Попытаться найти пользователя (вернёт 404)
curl http://localhost:8000/api/v1/users/1
```

### Проверка через pytest

```bash
# Запустить все тесты
pytest tests/

# Запустить только тесты пользователей
pytest tests/api/v1/controllers/test_users.py -v

# Запустить с покрытием
pytest --cov=app --cov-branch --cov-report=term-missing
```

---

## Production

### Применение миграций в production

```bash
# Через Docker Compose
docker-compose exec web alembic upgrade head

# Проверить статус миграций
docker-compose exec web alembic current
```

### Мониторинг

После деплоя следить за:
- Количество деактивированных пользователей: `SELECT COUNT(*) FROM users WHERE is_active = false;`
- Ошибки API при попытке деактивировать несуществующего пользователя
- Производительность эндпоинта DELETE (должен быть < 1 сек согласно SC-001)

---

## Полезные команды

```bash
# Создать миграцию
alembic revision -m "add is_active field to users"

# Применить миграцию
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# Показать историю миграций
alembic history

# Проверить текущую версию
alembic current

# Сгенерировать SQL для миграции (без применения)
alembic upgrade head --sql
```

---

## Часто задаваемые вопросы

**Q: Можно ли реактивировать пользователя?**

A: Нет, функциональность реактивации не входит в текущую задачу. Это будет реализовано в отдельной фиче при необходимости.

**Q: Что происходит с сессиями деактивированного пользователя?**

A: Сессии обрабатываются отдельно от этой фичи. При следующей попытке аутентификации пользователь не сможет войти.

**Q: Как найти деактивированного пользователя в БД?**

A: Используйте прямой SQL запрос: `SELECT * FROM users WHERE is_active = false;`

**Q: Можно ли физически удалить пользователя?**

A: Нет, функциональность физического удаления не реализована. Только деактивация.

---

## Следующие шаги

1. ✅ Миграция применена
2. ✅ Код имплементирован
3. ✅ Тесты написаны и проходят
4. ➡️ Создать Pull Request
5. ➡️ Замержить в main после code review

---

**Статус**: ✅ Quickstart Guide готов к использованию
