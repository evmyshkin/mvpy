# Quickstart: Update User via API

**Feature**: 002-update-user
**Date**: 2025-02-05

Этот документ предоставляет практическое руководство для разработки, тестирования и деплоя фичи обновления пользователя.

## Предварительные требования

### Необходимое ПО

- Python 3.13+
- UV пакетный менеджер
- PostgreSQL 17
- Docker и Docker Compose (опционально, для контейнеризированного запуска)

### Установка зависимостей

```bash
# Установка зависимостей проекта
uv sync

# Установка speckit (если ещё не установлено)
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

## Локальная разработка

### 1. Запуск PostgreSQL

**Вариант A: Через Docker Compose (рекомендуется)**

```bash
# Запуск PostgreSQL в контейнере
make up
# или
docker-compose up -d

# Проверка статуса
docker-compose ps
```

**Вариант B: Локальная PostgreSQL**

```bash
# Убедитесь, что PostgreSQL 17 установлен и запущен
# Создайте БД:
createdb mvpy_local

# Настройте .env файл (см. .env.example)
cp .env.example .env
# Отредактируйте POSTGRES__HOST, POSTGRES__PORT, etc.
```

### 2. Применение миграций БД

```bash
# Применить все миграции
alembic upgrade head

# Проверить статус миграций
alembic current
alembic history
```

### 3. Запуск приложения

```bash
# С hot reload для разработки
make dev
# или
uv run uvicorn app.main:app --reload

# Без hot reload
uv run uvicorn app.main:app
```

Приложение будет доступно на `http://localhost:8000`

API документация (Swagger UI): `http://localhost:8000/docs`

## Тестирование

### 1. Запуск всех тестов

```bash
# Запуск с покрытием
make test
# или
pytest --cov=app --cov-branch --cov-report=term-missing

# Запуск с выводом print statements
pytest -s
```

### 2. Запуск конкретного теста

```bash
# Запуск конкретного теста
pytest tests/api/v1/controllers/test_users.py::test_update_user_success

# Запуск всех тестов в файле
pytest tests/api/v1/controllers/test_users.py

# Запуск с подробным выводом
pytest -vv tests/api/v1/controllers/test_users.py::test_update_user_success
```

### 3. Запуск тестов для конкретного слоя

```bash
# API (controllers) тесты
pytest tests/api/v1/controllers/test_users.py -k update

# Service тесты
pytest tests/services/test_user_service.py -k update

# Все update тесты
pytest -k update_user
```

### 4. Проверка покрытия

```bash
# HTML отчет покрытия
pytest --cov=app --cov-branch --cov-report=html

# Открыть отчет
open htmlcov/index.html
```

## Ручное тестирование API

### 1. Создание тестового пользователя

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Тест",
    "last_name": "Тестов",
    "password": "Test12345"
  }'
```

Ожидаемый ответ:
```json
{
  "id": 1,
  "email": "test@example.com",
  "first_name": "Тест",
  "last_name": "Тестов"
}
```

### 2. Обновление пользователя (все поля)

```bash
curl -X PUT http://localhost:8000/api/v1/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com",
    "first_name": "Иван",
    "last_name": "Иванов",
    "password": "NewSecure123"
  }'
```

Ожидаемый ответ:
```json
{
  "id": 1,
  "email": "newemail@example.com",
  "first_name": "Иван",
  "last_name": "Иванов"
}
```

### 3. Частичное обновление (только email)

```bash
curl -X PUT http://localhost:8000/api/v1/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "email": "another@example.com"
  }'
```

### 4. Обновление с невалидными данными

```bash
# Невалидный email и имя с цифрами
curl -X PUT http://localhost:8000/api/v1/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "email": "invalid-email",
    "first_name": "John123"
  }'
```

Ожидаемый ответ (422) с локализованными ошибками:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Некорректный формат email",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "first_name"],
      "msg": "Должно содержать только русские/английские буквы и тире",
      "type": "value_error"
    }
  ]
}
```

### 5. Попытка duplicate email

```bash
# Создать второго пользователя
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "existing@example.com",
    "first_name": "Петр",
    "last_name": "Петров",
    "password": "Test12345"
  }'

# Попытка обновить первого пользователя с email второго
curl -X PUT http://localhost:8000/api/v1/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "email": "existing@example.com"
  }'
```

Ожидаемый ответ (400):
```json
{
  "detail": "Пользователь с таким email уже существует"
}
```

### 6. Обновление несуществующего пользователя

```bash
curl -X PUT http://localhost:8000/api/v1/users/999 \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Тест"
  }'
```

Ожидаемый ответ (404):
```json
{
  "detail": "Пользователь не найден"
}
```

## Качество кода

### 1. Pre-commit hooks

```bash
# Установка hooks
pre-commit install

# Ручной запуск всех проверок
pre-commit run --all-files

# Запуск проверок для изменённых файлов
pre-commit run
```

### 2. Ruff (линтер и форматтер)

```bash
# Проверка кода
ruff check app/

# Исправление ошибок
ruff check --fix app/

# Форматирование кода
ruff format app/
```

### 3. MyPy (тайпинг)

```bash
# Проверка типов
mypy app/

# Проверка конкретного файла
mypy app/api/v1/controllers/users.py
```

## Структура кода

### Файлы для создания/изменения

```
app/
├── api/
│   └── v1/
│       ├── controllers/
│       │   └── users.py          # ДОБАВИТЬ: PUT /{user_id} endpoint
│       └── schemas/
│           └── users.py          # ДОБАВИТЬ: UserUpdateRequest, UserUpdateResponse
├── services/
│   └── user_service.py           # ДОБАВИТЬ: update_user() method
└── db/
    └── crud/
        └── users.py              # ИСПОЛЬЗОВАТЬ: BaseCrud.update_one_or_none()

tests/
├── api/
│   └── v1/
│       └── controllers/
│           └── test_users.py     # ДОБАВИТЬ: тесты для PUT /{user_id}
├── services/
│   └── test_user_service.py      # ДОБАВИТЬ: тесты для update_user()
└── conftest.py                   # РАСШИРИТЬ: фикстуры для update
```

### Пример реализации (скелет)

```python
# app/api/v1/schemas/users.py

class UserUpdateRequest(BaseModel):
    """Схема запроса на обновление пользователя."""

    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Валидация имени/фамилии.

        Args:
            v: Значение поля (first_name или last_name)

        Returns:
            Валидированное значение

        Raises:
            ValueError: Если значение содержит недопустимые символы
                или превышает 100 символов
        """
        if v is None:
            return v
        if not re.match(r'^[А-Яа-яA-Za-z\-]+$', v):
            raise ValueError(
                'Должно содержать только русские/английские буквы и тире'
            )
        if len(v) > 100:
            raise ValueError('Длина не должна превышать 100 символов')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str | None) -> str | None:
        """Валидация длины пароля.

        Args:
            v: Значение поля password

        Returns:
            Валидированное значение

        Raises:
            ValueError: Если длина пароля меньше 8 или больше 100 символов
        """
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        if len(v) > 100:
            raise ValueError('Пароль не должен превышать 100 символов')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, v: str | None) -> str | None:
        """Валидация сложности пароля.

        Args:
            v: Значение поля password

        Returns:
            Валидированное значение

        Raises:
            ValueError: Если пароль не содержит заглавную букву,
                строчную букву или цифру
        """
        if v is None:
            return v
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


class UserUpdateResponse(BaseModel):
    """Схема ответа при обновлении пользователя."""

    id: int
    email: str
    first_name: str
    last_name: str
```

```python
# app/services/user_service.py

class UserService(BaseService):
    async def update_user(
        self,
        session: AsyncSession,
        user_id: int,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        password: str | None = None,
    ) -> UserUpdateResponse:
        """Обновить пользователя.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя для обновления
            email: Новый email (опционально)
            first_name: Новое имя (опционально)
            last_name: Новая фамилия (опционально)
            password: Новый пароль (опционально)

        Returns:
            Схема обновлённого пользователя

        Raises:
            HTTPException: 404 если пользователь не найден
            HTTPException: 400 если email уже существует
        """
        # Логика обновления
        pass
```

```python
# app/api/v1/controllers/users.py

@router.put('/{user_id}', response_model=UserUpdateResponse, status_code=200)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: AsyncSession = Depends(connector.get_session),
) -> UserUpdateResponse:
    """Обновить пользователя.

    Args:
        user_id: ID пользователя
        user_data: Данные для обновления
        db: Сессия БД

    Returns:
        Обновлённые данные пользователя
    """
    return await user_service.update_user(
        session=db,
        user_id=user_id,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        password=user_data.password,
    )
```

## Важные требования к реализации

### Локализация валидационных ошибок

**КРИТИЧЕСКИ ВАЖНО**: Все сообщения об ошибках валидации в Pydantic схемах должны быть на русском языке. Это требуется принципом XI конституции ("Документация и локализация").

Примеры правильных сообщений об ошибках:

```python
# ✅ ПРАВИЛЬНО - на русском
raise ValueError('Должно содержать только русские/английские буквы и тире')
raise ValueError('Пароль должен содержать минимум 8 символов')
raise ValueError('Пароль должен содержать минимум 1 заглавную букву')

# ❌ НЕПРАВИЛЬНО - на английском
raise ValueError('Must contain only letters and hyphens')
raise ValueError('Password must be at least 8 characters')
```

### Переиспользование валидаторов

Валидаторы из UserCreateRequest должны быть переиспользованы в UserUpdateRequest:

1. Вынести общие валидаторы в отдельные функции
2. Или создать базовый класс с валидаторами
3. Или использовать миксин

## Полезные команды

### Работа с БД

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "description"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# Посмотреть текущую версию
alembic current

# Посмотреть историю миграций
alembic history
```

### Docker

```bash
# Собрать образы
docker-compose build

# Запустить контейнеры
docker-compose up -d

# Остановить контейнеры
docker-compose down

# Посмотреть логи
docker-compose logs -f

# Перезапустить контейнеры
docker-compose restart
```

### Git

```bash
# Статус изменений
git status

# Добавить изменения
git add .

# Коммит
git commit -m "feat: add update user endpoint"

# Пуш в origin
git push origin 002-update-user
```

## Troubleshooting

### Проблема: Migration conflicts

**Решение**:
```bash
# Откатить к базе
alembic downgrade base

# Удалить конфликтующие миграции
rm migrations/versions/xxx_conflicting_migration.py

# Пересоздать миграцию
alembic revision --autogenerate -m "description"
```

### Проблема: Тесты падают с "Database is locked"

**Решение**:
```bash
# Убить все процессы Python
pkill -f python

# Перезапустить PostgreSQL
docker-compose restart db

# Запустить тесты снова
pytest
```

### Проблема: Port 8000 already in use

**Решение**:
```bash
# Найти процесс
lsof -i :8000

# Убить процесс
kill -9 <PID>

# Или использовать другой порт
uv run uvicorn app.main:app --port 8001
```

## Дальнейшие шаги

После завершения имплементации:

1. **Запуск всех тестов**: `make test`
2. **Pre-commit проверки**: `pre-commit run --all-files`
3. **Проверка покрытия**: `pytest --cov=app --cov-branch --cov-report=html`
4. **Ручное тестирование**: проверить все сценарии из этого документа
5. **Проверка локализации**: убедиться, что все ошибки на русском языке
6. **Ревью кода**: запросить code review у команды
7. **Мёрж в main**: после одобрения ревью

## Дополнительная документация

- [Конституция проекта](../../../.specify/memory/constitution.md)
- [Спецификация фичи](./spec.md)
- [План имплементации](./plan.md)
- [Data Model](./data-model.md)
- [Research](./research.md)
- [OpenAPI контракт](./contracts/update_user.yaml)
- [CLAUDE.md](../../../CLAUDE.md)
- [README](../../../README.md)