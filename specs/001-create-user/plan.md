# Implementation Plan: Создание пользователя через API

**Branch**: `001-create-user` | **Date**: 2026-02-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-create-user/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Создание REST API endpoint для регистрации пользователей с хешированием паролей. Пользователи идентифицируются по уникальному email (поле username отсутствует). API должно поддерживать валидацию данных (email, имя/фамилия с ограничением на русские/английские буквы и тире, сложность пароля), возврат статусов 201/409/422, и обеспечение производительности 100 req/s при p95 < 500ms.

## Technical Context

**Language/Version**: Python 3.13 (обязательно по конституции)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic V2, Alembic, AsyncPG, bcrypt==4.0.1, passlib[bcrypt]
**Storage**: PostgreSQL 17 (AsyncPG driver)
**Testing**: pytest, pytest-asyncio, pytest-cov, Faker
**Target Platform**: Linux server (Docker)
**Project Type**: web (FastAPI backend service)
**Performance Goals**: 100 req/s, p95 < 500ms (из SC-001, SC-002)
**Constraints**:
- Обязательная асинхронность (SQLAlchemy 2.0+, AsyncPG)
- Соблюдение чистой архитектуры: Controller → Service → CRUD → DB
- Использование BaseCrud, BaseDBModel, BaseService
- Хеширование паролей через passlib с bcrypt==4.0.1 (версия фиксирована для совместимости)
**Scale/Scope**: один endpoint POST /api/v1/users/, 1 таблица users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Технологический стек (Принцип I)
✅ **Python 3.13** - требуется конституцией
✅ **FastAPI** - требуется конституцией для API endpoints
✅ **SQLAlchemy 2.0+ с AsyncPG** - требуется конституцией
✅ **Pydantic V2** - требуется конституцией для валидации
✅ **Alembic** - требуется конституцией для миграций
✅ **PostgreSQL 17** - требуется конституцией
✅ **UV** - требуется конституцией как пакетный менеджер

### Dependency Injection (Принцип II)
✅ FastAPI Depends для DI сессий БД и сервисов

### Type Annotations (Принцип III)
✅ Строгая типизация для всех функций и методов

### Управление конфигурацией (Принцип IV)
✅ Pydantic V2 Settings с `__` разделителем для nested config

### Чистая архитектура (Принцип V)
✅ Controller (`app/api/v1/controllers/users.py`) → Service (`app/services/user_service.py`) → CRUD (`app/db/crud/users.py`) → Model (`app/db/models/user.py`)

### Абстракция базовых классов (Принцип VI)
✅ BaseDBModel для SQLAlchemy модели
✅ BaseCrud[User] для CRUD операций
✅ BaseService для бизнес-логики
✅ BaseSchema для Pydantic моделей

### Управление сессиями БД (Принцип VII)
✅ connector.get_session() для асинхронных сессий
✅ Автоматический выбор URI для окружений (LOCAL/DEV/STAGE/PROD/PYTEST)

### Требования к тестированию (Принцип VIII)
✅ pytest-asyncio для асинхронных тестов
✅ Faker для тестовых данных
✅ Покрытие ветвлений (--cov-branch)
✅ Структура тестов зеркалит app/
✅ Обязательный запуск make test после изменений

### Стандарты качества кода (Принцип IX)
✅ Ruff с полным набором правил
✅ MyPy с pydantic plugin
✅ Одинарные кавычки, 100 символов длина строки
✅ Google-style docstrings на русском
✅ Pre-commit hooks

### Дисциплина scoped-разработки (Принцип X)
✅ Только создание пользователя, без авторизации/обновления/удаления (YAGNI)

### Документация и локализация (Принцип XI)
✅ Docstrings на русском (Google style)
✅ Не читать .env, использовать .env.example

### Принципы проектирования API (Принцип XII)
✅ Router: app/api/v1/router.py включает роутер users
✅ Версионирование: префикс /v1
✅ Healthcheck на корневом пути /
✅ BaseCRUD автоматически raise HTTPException
✅ starlette.status для HTTP кодов

### Git-ветвление (Принцип XIII)
✅ Ветка 001-create-user от main

### Миграции БД (Архитектурные стандарты)
✅ Автогенерация схематической миграции через alembic revision --autogenerate
✅ Импорт модели в app/db/models/__init__.py для обнаружения Alembic

**GATE STATUS**: ✅ PASSED - все требования конституции соблюдены

## Project Structure

### Documentation (this feature)

```text
specs/001-create-user/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── openapi.yaml     # OpenAPI 3.0 spec for user creation endpoint
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
app/
├── api/
│   ├── v1/
│   │   ├── controllers/
│   │   │   ├── __init__.py
│   │   │   └── users.py          # POST /api/v1/users/ endpoint
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── users.py          # UserCreateRequest, UserCreateResponse
│   │   └── router.py             # Include users router
│   └── router.py                 # Main API router (already exists)
├── db/
│   ├── base.py                   # BaseDBModel (already exists)
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── base.py               # BaseCrud (already exists)
│   │   └── users.py              # UserCrud extends BaseCrud[User]
│   ├── models/
│   │   ├── __init__.py           # Import User for Alembic
│   │   └── user.py               # User SQLAlchemy model
│   └── session.py                # connector.get_session (already exists)
├── schemas/
│   ├── __init__.py               # Base schemas (already exists)
│   └── base.py                   # BaseSchema (already exists)
└── services/
    ├── __init__.py
    ├── base.py                   # BaseService (already exists)
    └── user_service.py           # UserService extends BaseService

tests/
├── api/
│   └── v1/
│       └── controllers/
│           └── test_users.py     # Test user creation endpoint
├── db/
│   └── crud/
│       └── test_users_crud.py    # Test UserCrud operations
└── services/
    └── test_user_service.py      # Test UserService logic

migrations/versions/
└── [timestamp]_create_users_table.py  # Alembic migration

requirements/  # or pyproject.toml if using UV
└── dev.txt    # Add passlib[bcrypt] if not present
```

**Structure Decision**: Выбрана структура web-приложения (FastAPI backend) в соответствии с конституцией. Все слои следуют чистой архитектуре Controller → Service → CRUD → DB. Тесты зеркалят структуру app/.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Все требования конституции соблюдены | - |

---

## Phase 0: Research & Best Practices

### Research Tasks

1. **Проверка зависимостей для хеширования паролей**
   - passlib[bcrypt] должен быть добавлен в зависимости
   - passlib обеспечивает безопасный bcrypt с автоматической солью
   - Альтернативы: bcrypt (прямо), argon2 (более новый, но менее совместим)
   - Решение: passlib[bcrypt] как industry standard

2. **Pydantic V2 валидация для first_name/last_name (русские/английские буквы и тире)**
   - Использовать @field_validator с regex pattern
   - Regex: `^[А-Яа-яA-Za-z\-]+$` для кириллицы, латиницы и тире
   - Pydantic 2.x использует pytest-analyzed validators в отличие от 1.x
   - Не использовать @root_validator для отдельных полей

3. **Валидация сложности пароля**
   - Использовать Pydantic field_validator с regex
   - Regex: `^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$`
   - Или использовать отдельный validator для читаемости ошибок
   - Решение: отдельные валидаторы для каждого требования для лучших error messages

4. **Обработка race condition при дубликатах email**
   - SQLAlchemy уникальный constraint на email column
   - IntegrityError от PostgreSQL 409 статус
   - BaseCrud должен обрабатывать IntegrityError

5. **Тестирование с PostgreSQL в pytest-asyncio**
   - Использовать fixtures для асинхронной сессии БД
   - Rollback после каждого теста для изоляции
   - Faker для генерации test data

### Best Practices Researched

**FastAPI endpoint design**:
- POST /api/v1/users/ для создания (REST collection naming)
- status 201 с Location header при успехе
- status 409 Conflict для дубликата email
- status 422 Validation Error для невалидных данных

**SQLAlchemy async patterns**:
- AsyncSession для асинхронных операций
- select() instead of query() для SQLAlchemy 2.0+
- await session.commit() для транзакций

**Security**:
- bcrypt cost factor: 12 (default in passlib)
- Не логировать пароли (даже захешированные)
- Password field не должен возвращаться в response

---

## Phase 1: Design & Contracts

### Data Model

См. [data-model.md](./data-model.md)

### API Contracts

См. [contracts/openapi.yaml](./contracts/openapi.yaml)

### Quickstart

См. [quickstart.md](./quickstart.md)

---

## Phase 2: Implementation Tasks

См. [tasks.md](./tasks.md) для детального списка задач имплементации.

---

## Agent Context Update

После завершения Phase 1 выполнить:
```bash
.specify/scripts/bash/update-agent-context.sh claude
```

Это обновит `.claude/custom_instructions.md` с технологиями из текущего плана.