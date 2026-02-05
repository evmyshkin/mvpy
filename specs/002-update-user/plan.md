# Implementation Plan: Update User via API

**Branch**: `002-update-user` | **Date**: 2025-02-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-update-user/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Реализовать API-эндпоинт для обновления информации о существующих пользователях в системе. Фича позволяет клиентам API обновлять поля first_name, last_name, password и email пользователей через PUT-запрос. Система должна валидировать входные данные (формат email, сложность пароля, допустимые символы в именах), обеспечивать уникальность email, хешировать пароли и возвращать соответствующие HTTP статусы (200, 400, 404, 422). Технический подход базируется на существующей архитектуре CRUD → Service → Controller с использованием BaseCrud, BaseService и Pydantic схем.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic V2, Alembic, AsyncPG, bcrypt 4.0.1 + passlib
**Storage**: PostgreSQL 17
**Testing**: pytest, pytest-asyncio, Faker
**Target Platform**: Linux server (LOCAL/DEV/STAGE/PROD окружения)
**Project Type**: web (FastAPI REST API сервис)
**Performance Goals**:
- Обновление пользователя: < 2 секунд
- Валидация и возврат ошибок: < 500 миллисекунд
**Constraints**:
- Хеширование паролей обязательно (plaintext не хранится)
- Email должен быть уникальным в системе
- Имена (first_name, last_name): только буквы (кириллица/латиница) и дефисы
- Пароль: минимум 8 символов, минимум 1 заглавная, 1 строчная буква и 1 цифра
**Scale/Scope**:
- API-эндпоинт: PUT /api/v1/users/{user_id}
- Использует существующую модель User
- Расширяет существующий CRUD, Service и Controller слои

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Принципы конституции

✅ **I. Технологический стек**
- FastAPI для API endpoints
- Python 3.13 (обязательно)
- SQLAlchemy 2.0+ с AsyncPG
- Pydantic V2 с Annotated типизацией
- Alembic для миграций
- PostgreSQL 17
- bcrypt 4.0.1 через passlib для хеширования паролей
- UV как пакетный менеджер

✅ **II. Dependency Injection**
- Использовать FastAPI Depends для всех зависимостей
- В контроллере использовать Depends(connector.get_session())

✅ **III. Type Annotations**
- Строгая типизация для всех функций, методов и переменных

✅ **IV. Управление конфигурацией**
- Pydantic V2 Settings с Annotated типизацией
- Разделитель `__` для вложенных переменных окружения

✅ **V. Чистая архитектура**
- Controller → Service → CRUD → DB слои
- Контроллер: обработчик PUT маршрута, dependency injection, вызов service или crud
- Service: бизнес-логика валидации email uniqueness, хеширования пароля
- CRUD: операция update_one_or_none из BaseCrud
- Model: существующая User модель

✅ **VI. Абстракция базовых классов**
- Использовать BaseCrud[User] для операции update
- Использовать BaseService (или UserService если существует) для бизнес-логики
- Использовать BaseDBModel (User уже наследуется от неё)
- Не добавлять функциональность в Base-классы

✅ **VII. Управление сессиями БД**
- Использовать Depends(connector.get_session()) в контроллере
- Коннектор автоматически выбирает URI для окружения

✅ **VIII. Требования к тестированию**
- pytest-asyncio для асинхронных тестов
- Faker для генерации тестовых данных
- Pydantic модели для создания тестовых данных
- Фикстуры в conftest.py (расширить существующие)
- Покрытие ветвлений (--cov-branch)
- Структура тестов зеркалит структуру app/
- Обязательный workflow: написать тесты → запустить make test → pre-commit hooks

✅ **IX. Стандарты качества кода**
- Ruff с полным набором правил
- MyPy с плагином Pydantic
- Одинарные кавычки, пробельные отступы, длина строки 100 символов
- Google-style docstrings на русском языке
- Pre-commit hooks

✅ **X. Дисциплина scoped-разработки**
- Только то, что требуется в spec.md
- Не добавлять функционала "на будущее"
- Следовать YAGNI

✅ **XI. Документация и локализация**
- Все .md файлы на русском
- Docstrings на русском (Google-style)
- Не читать .env, использовать .env.example

✅ **XII. Принципы проектирования API**
- PUT /api/v1/users/{user_id} для обновления
- Использовать starlette.status для HTTP статусов
- Логика только в Service или CRUD, не в контроллере
- BaseCRUD автоматически raise HTTPException

✅ **XIII. Git-ветвление**
- Ветка 002-update-user (уже создана)
- Сквозная нумерация фичей

✅ **XIV. SQLAlchemy**
- Использовать select() для получения данных
- Использовать update() для обновлений (через BaseCrud.update_one_or_none)

✅ **XV. OpenAPI документация**
- FastAPI генерирует автоматически
- Тестировать openapi не нужно

✅ **XVI. Конфигурация окружений**
- LOCAL, DEV, STAGE, PROD, PYTEST
- Коннектор автоматически выбирает URI

### Gate Result

**✅ PASSED**: Все принципы конституции соблюдены. Нет нарушений, требующих обоснования.

## Project Structure

### Documentation (this feature)

```text
specs/002-update-user/
├── plan.md              # Этот файл
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── update_user.yaml # OpenAPI контракт для PUT /users/{id}
└── tasks.md             # Phase 2 output (создаётся через /speckit.tasks)
```

### Source Code (repository root)

```text
app/
├── api/
│   └── v1/
│       ├── controllers/
│       │   └── users.py          # ДОБАВИТЬ: PUT /{user_id} endpoint
│       └── schemas/
│           └── users.py          # ДОБАВИТЬ: UserUpdateRequest, UserUpdateResponse
├── db/
│   ├── crud/
│   │   └── users.py              # ИСПОЛЬЗОВАТЬ: BaseCrud.update_one_or_none()
│   └── models/
│       └── user.py               # ИСПОЛЬЗОВАТЬ: существующая User модель
└── services/
    └── user_service.py           # ДОБАВИТЬ: бизнес-логика валидации email uniqueness, хеширования пароля

tests/
├── api/
│   └── v1/
│       └── controllers/
│           └── test_users.py     # ДОБАВИТЬ: тесты для PUT /{user_id}
├── services/
│   └── test_user_service.py      # ДОБАВИТЬ: тесты для update логики
└── conftest.py                   # РАСШИРИТЬ: добавить фикстуры для update user
```

**Structure Decision**: Выбрана структура "Web application (backend only)" - FastAPI REST API сервис. Структура соответствует существующей архитектуре проекта из constitution.md: Controller → Service → CRUD → DB слои. Новая функциональность расширяет существующие модули (users controller, user_service, users CRUD) без создания новых директорий.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Нарушений конституции нет, данный раздел не заполняется.