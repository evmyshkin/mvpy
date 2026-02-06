# Quick Start: Аутентификация и авторизация

**Фича**: 005-authenticate-user
**Дата**: 2025-02-06

## Обзор

Это руководство поможет вам быстро запустить проект локально и протестировать функцию аутентификации и авторизации.

## Предварительные требования

- Python 3.13
- PostgreSQL 17
- UV пакетный менеджер
- Git

## Шаг 1: Клонирование и настройка

```bash
# Клонировать репозиторий
git clone <repository-url>
cd mvpy

# Переключиться на ветку фичи
git checkout 005-authenticate-user

# Установить зависимости
uv sync

# Активировать виртуальное окружение
source .venv/bin/activate  # Linux/macOS
# или
.venv\Scripts\activate     # Windows
```

## Шаг 2: Настройка переменных окружения

Создать файл `.env` в корне проекта (см. `.env.example` для reference):

```bash
# База данных
POSTGRES__HOST=localhost
POSTGRES__PORT=5432
POSTGRES__USER=postgres
POSTGRES__PASSWORD=postgres
POSTGRES__DB=mvpy_local

# JWT (добавить для этой функции)
JWT__SECRET_KEY=your-secret-key-min-32-characters-long
JWT__ACCESS_TOKEN_EXPIRE_MINUTES=60

# Окружение
ENVIRONMENT=local
```

**Важно**: Генерировать уникальный `JWT__SECRET_KEY` для каждого окружения:

```bash
# Генерация случайного ключа (Linux/macOS)
openssl rand -hex 32

# Или через Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Шаг 3: Запуск PostgreSQL

### Вариант A: Docker Compose (рекомендуется)

```bash
# Запустить PostgreSQL в Docker
docker-compose up -d postgres

# Проверить статус
docker-compose ps
```

### Вариант B: Локальная установка

```bash
# Создать базу данных
createdb mvpy_local

# Или через psql
psql -U postgres -c "CREATE DATABASE mvpy_local;"
```

## Шаг 4: Применение миграций БД

```bash
# Применить все миграции
alembic upgrade head

# Проверить статус миграций
alembic current
```

Ожидаемый вывод:
```
INFO  [alembic.runtime.migration] Running upgrade-> 005_add_blacklisted_tokens
```

## Шаг 5: Запуск приложения

### Вариант A: С hot reload (для разработки)

```bash
make dev
# или
uv run uvicorn app.main:app --reload
```

### Вариант B: Обычный запуск

```bash
uv run uvicorn app.main:app
```

Приложение будет доступно по адресу: `http://localhost:8000`

## Шаг 6: Проверка работоспособности

### 6.1. Доступ к API документации

Открыть в браузере:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Healthcheck: http://localhost:8000/

### 6.2. Создание тестового пользователя

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "first_name": "Иван",
    "last_name": "Иванов",
    "password": "Password123",
    "repeat_password": "Password123"
  }'
```

Ожидаемый ответ:
```json
{
  "id": 1,
  "email": "test@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "is_active": true,
  "created_at": "2025-02-06T12:34:56.123456",
  "updated_at": "2025-02-06T12:34:56.123456"
}
```

### 6.3. Аутентификация

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password123"
  }'
```

Ожидаемый ответ:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Сохранить `access_token` для следующих запросов.

### 6.4. Проверка защищённых эндпоинтов

Все эндпоинты работы с пользователями (кроме создания) требуют авторизации:

```bash
TOKEN="сохранённый_токен"

# Получить пользователя по ID
curl -X GET "http://localhost:8000/api/v1/users/1" \
  -H "Authorization: Bearer $TOKEN"

# Получить список всех пользователей
curl -X GET "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer $TOKEN"

# Обновить пользователя
curl -X PUT "http://localhost:8000/api/v1/users/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com",
    "first_name": "Пётр",
    "last_name": "Петров"
  }'
```

Пример ответа для GET запроса:
```json
{
  "id": 1,
  "email": "test@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "is_active": true
}
```

### 6.5. Выход из системы

```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer $TOKEN"
```

Ожидаемый ответ:
```json
{
  "message": "Успешный выход из системы"
}
```

### 6.6. Проверка отозванного токена

```bash
curl -X GET "http://localhost:8000/api/v1/users/1" \
  -H "Authorization: Bearer $TOKEN"
```

Ожидаемый ответ (401 Unauthorized):
```json
{
  "detail": "Токен отозван"
}
```

## Шаг 7: Запуск тестов

```bash
# Запустить все тесты
make test
# или
pytest --cov=app --cov-branch --cov-report=term-missing

# Запустить только auth тесты
pytest tests/api/v1/controllers/test_auth.py -v
pytest tests/services/test_auth_service.py -v

# Запустить с выводом print statements
pytest -s
```

Ожидаемый результат: все тесты проходят, покрытие > 90%.

## Шаг 8: Проверка качества кода

```bash
# Запустить pre-commit hooks
pre-commit run --all-files

# Или отдельно:
ruff check .
mypy app/
```

Ожидаемый результат: никаких ошибок или предупреждений.

## Troubleshooting

### Проблема: "Неверный email или пароль"

**Решение**:
- Проверить, что пользователь существует в БД
- Проверить, что `is_active=True`
- Проверить, что пароль соответствует требованиям (8+ символов, верхний/нижний регистр, цифра)

### Проблема: "Срок действия токена истёк"

**Решение**:
- Увеличить `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` в `.env`
- Перезапустить приложение
- Получить новый токен через `/auth/login`

### Проблема: "Токен отозван"

**Решение**:
- Токен был отозван через `/auth/logout`
- Получить новый токен через `/auth/login`

### Проблема: "Connection refused" при подключении к БД

**Решение**:
- Проверить, что PostgreSQL запущен: `docker-compose ps`
- Проверить параметры подключения в `.env`
- Проверить, что база данных создана: `psql -U postgres -l`

### Проблема: Миграции не применяются

**Решение**:
```bash
# Откатить и применить миграции заново
alembic downgrade base
alembic upgrade head

# Или проверить текущую версию
alembic current
alembic history
```

### Проблема: Тесты падают с "Database connection error"

**Решение**:
- Проверить, что переменная `ENVIRONMENT=pytest` установлена
- Проверить, что тестовая БД существует (отдельная от основной)
- Очистить тестовую БД: `psql -U postgres -c "DROP DATABASE IF EXISTS mvpy_test;"`

## Архитектура проекта

```
app/
├── api/v1/
│   ├── controllers/
│   │   ├── auth.py      # Эндпоинты login, logout
│   │   └── users.py     # Защищённые эндпоинты пользователей
│   ├── dependencies.py  # Dependency функции (get_current_user, get_token_data)
│   └── schemas/
│       └── auth.py      # Pydantic схемы для auth
├── db/
│   ├── models/
│   │   ├── blacklisted_token.py  # Модель отозванных токенов
│   │   └── user.py               # Модель пользователя
│   └── crud/
│       └── blacklisted_tokens.py # CRUD операции для токенов
├── services/
│   ├── auth_service.py        # Бизнес-логика аутентификации
│   ├── token_service.py       # Валидация JWT токенов
│   └── current_user_service.py # Получение текущего пользователя
└── config.py                  # JWT конфигурация
```

## Следующие шаги

1. **Изучить документацию**:
   - [Спецификация функции](./spec.md)
   - [План реализации](./plan.md)
   - [Модель данных](./data-model.md)
   - [API контракты](./contracts/auth.http)

2. **Начать разработку**:
   - Запустить `make dev` для hot reload
   - Открыть http://localhost:8000/docs для интерактивной документации
   - Изучать код в `app/api/v1/controllers/auth.py`

3. **Записать новые задачи**:
   - Использовать `/speckit.tasks` для генерации задач имплементации

## Полезные команды

```bash
# Смена ветки
git checkout 005-authenticate-user

# Обновление из main
git fetch origin main
git rebase origin/main

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1

# Создание новой миграции
alembic revision --autogenerate -m "описание"

# Запуск тестов
make test

# Проверка качества кода
pre-commit run --all-files

# Запуск приложения
make dev
```

## Дополнительные ресурсы

- [Документация FastAPI](https://fastapi.tiangolo.com/)
- [Документация JWT](https://jwt.io/)
- [Конституция проекта](../../.specify/memory/constitution.md)
- [Руководство разработчика](../../CLAUDE.md)