# Implementation Plan: Поиск пользователей через API

**Branch**: `004-user-search` | **Date**: 2025-02-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-user-search/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Реализовать API endpoint для поиска пользователей в системе с поддержкой двух сценариев:
1. Поиск конкретного пользователя по email (без учета регистра)
2. Получение списка всех пользователей

Все ответы API не должны содержать пароль пользователей. Система должна валидировать формат email и возвращать соответствующие HTTP статус коды (200, 404, 422) с сообщениями об ошибках на русском языке.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic V2, AsyncPG
**Storage**: PostgreSQL 17
**Testing**: pytest с pytest-asyncio, Faker
**Target Platform**: Linux server (веб-сервис)
**Project Type**: web (FastAPI backend service)
**Performance Goals**: <1 секунда для поиска по email, <2 секунд для списка до 10,000 пользователей
**Constraints**: Защита парольных данных (никогда не возвращать в API), валидация email RFC 5322
**Scale/Scope**: До 10,000 пользователей в базе, поддержка одновременных запросов от нескольких администраторов

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Технологический стек (Принцип I)
✅ **PASS**: Используется FastAPI, Python 3.13, SQLAlchemy 2.0+, Pydantic V2, AsyncPG, PostgreSQL 17
- Все компоненты соответствуют конституции
- bcrypt 4.0.1 уже используется для хеширования паролей в существующей модели User

### Dependency Injection (Принцип II)
✅ **PASS**: Будет использоваться FastAPI Depends для управления сессиями БД
- Существующий pattern с `connector.get_session()` будет применен

### Type Annotations (Принцип III)
✅ **PASS**: Все функции будут иметь строгую типизацию
- Будут использоваться Annotated типы от Pydantic V2

### Управление конфигурацией (Принцип IV)
✅ **PASS**: Конфигурация через Pydantic Settings уже реализована
- Коннектор БД автоматически выбирает URI на основе окружения

### Чистая архитектура (Принцип V)
✅ **PASS**: Будет следовать паттерну Controller → Service → CRUD → DB
- Controller: `app/api/v1/controllers/users.py` - новый GET endpoint
- Service: `app/services/user_service.py` - методы для поиска пользователей
- CRUD: `app/db/crud/users.py` - методы find_by_email и find_all
- Models: Существующая модель User

### Абстракция базовых классов (Принцип VI)
✅ **PASS**: Будут использоваться существующие BaseCrud и BaseService
- Не будет добавляться доменная логика в базовые классы

### Управление сессиями БД (Принцип VII)
✅ **PASS**: Будет использоваться `connector.get_session()`
- Автоматический выбор URI для PYTEST окружения

### Требования к тестированию (Принцип VIII)
✅ **PASS**: Будут написаны тесты с pytest-asyncio и Faker
- Использование Pydantic моделей для тестовых данных
- Вынос повторяющихся фикстур в conftest.py
- Покрытие всех сценариев (успех, не найдено, ошибка валидации)
- Запуск make test после реализации

### Стандарты качества кода (Принцип IX)
✅ **PASS**: Код будет соответствовать стандартам Ruff и MyPy
- Докстринги на русском языке (Google-style)
- Pre-commit hooks будут запущены

### Дисциплина scoped-разработки (Принцип X)
✅ **PASS**: Реализуется только запрошенный функционал
- Без избыточной пагинации на этом этапе
- Без аутентификации (отложено на будущие версии)

### Документация и локализация (Принцип XI)
✅ **PASS**: Сообщения об ошибках на русском языке
- Валидационные ошибки локализованы через Pydantic схемы
- Docstring-и на русском языке

### Принципы проектирования API (Принцип XII)
✅ **PASS**: GET endpoint в `/api/v1/users/`
- Использование HTTP статусов из starlette.status
- Минимальная логика в контроллере (вызов сервиса)

### Git-ветвление (Принцип XIII)
✅ **PASS**: Ветка `004-user-search` создана по сквозной нумерации

### SQLAlchemy (Принцип XIV)
✅ **PASS**: Будет использоваться `select()` для запросов
- Производительность для больших списков

### Дополнительная документация openapi (Принцип XV)
✅ **PASS**: Openapi спецификация не тестируется
- FastAPI генерирует её автоматически

### Конфигурация окружений (Принцип XVI)
✅ **PASS**: Используется существующая конфигурация
- PYTEST окружение с отдельной БД

### Код-стиль (Принцип XVII)
✅ **PASS**: Использование именованных аргументов
- Тексты сообщений в Enum
- Импорты на уровне модуля

### Сервисный слой (Принцип XVIII)
✅ **PASS**: Сервисы будут принимать Pydantic схемы
- Использование model_dump() для передачи данных в CRUD

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
app/
├── api/
│   └── v1/
│       ├── controllers/
│       │   └── users.py          # Добавлен GET / endpoint для поиска
│       └── schemas/
│           └── users.py          # Добавлены схемы ответа для поиска
├── db/
│   ├── crud/
│   │   └── users.py              # Добавлены методы find_by_email, find_all
│   └── models/
│       └── user.py               # Существующая модель (без изменений)
└── services/
    └── user_service.py           # Добавлены методы для поиска пользователей

tests/
├── api/
│   └── v1/
│       └── controllers/
│           └── test_users.py     # Тесты для GET endpoint
└── services/
    └── test_user_service.py      # Тесты для методов поиска
```

**Structure Decision**: Выбрана структура web-приложения (FastAPI backend) в соответствии с конституцией. Все изменения следуют существующей архитектуре Controller → Service → CRUD → DB.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
