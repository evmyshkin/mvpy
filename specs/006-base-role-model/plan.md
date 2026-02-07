# План имплементации: Базовая ролевая модель

**Ветка**: `006-base-role-model` | **Дата**: 2025-02-07 | **Спек**: [spec.md](./spec.md)
**Входные данные**: Спецификация функции из `/specs/006-base-role-model/spec.md`

## Summary

Реализовать базовую ролевую модель для системы с тремя ролями (пользователь, менеджер, администратор), создать администратора по умолчанию при развертывании, автоматически присваивать роль "пользователь" при регистрации и проверять роль при каждом аутентифицированном запросе. Технический подход включает создание модели Role, связь User-Role через ForeignKey, миграцию для создания ролей и сервисный слой для работы с ролями.

## Technical Context

**Язык/Версия**: Python 3.13
**Основные зависимости**: FastAPI, SQLAlchemy 2.0+, Alembic, Pydantic V2, AsyncPG
**Хранилище**: PostgreSQL 17
**Тестирование**: pytest-asyncio, Faker
**Целевая платформа**: Linux server (LOCAL/DEV/STAGE/PROD окружения)
**Тип проекта**: Web API (single backend)
**Цели производительности**: Проверка роли не должна добавлять измеримой задержки к ответам API
**Ограничения**: <200ms p95 для стандартных API запросов с проверкой роли
**Масштаб**: 3 роли в справочнике, 1 администратор по умолчанию, автоматическая роль для всех новых пользователей

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Принцип I: Технологический стек
- **Python 3.13**: Да, указан в Technical Context
- **FastAPI**: Да, используется для API endpoints
- **SQLAlchemy 2.0+ с асинхронной поддержкой**: Да, для работы с БД
- **Pydantic V2**: Да, для валидации данных
- **Alembic**: Да, для миграций БД
- **PostgreSQL 17**: Да, основная СУБД
- **UV**: Да, пакетный менеджер

### ✅ Принцип II: Dependency Injection
- Использовать FastAPI Depends для зависимостей
- Явное объявление зависимостей

### ✅ Принцип V: Чистая архитектура
- Controller → Service → CRUD → DB разделение
- Controllers: `app/api/v1/controllers/`
- Services: `app/services/`
- CRUD: `app/db/crud/`
- Models: `app/db/models/`

### ✅ Принцип VI: Абстракция базовых классов
- BaseDBModel для моделей
- BaseCrud[ModelType] для CRUD операций
- BaseService для бизнес-логики

### ✅ Принцип VII: Управление сессиями БД
- Использовать `connector.get_session()` dependency
- Автоматический выбор URI БД по окружению

### ✅ Принцип VIII: Требования к тестированию
- pytest-asyncio для асинхронных тестов
- Faker для тестовых данных
- Pydantic модели для создания тестовых данных
- Покрытие ветвлений (--cov-branch)
- Обязательный запуск тестов после изменений

### ✅ Принцип XI: Документация и локализация
- Все .md файлы на русском языке
- Докстринги на русском языке (Google-style)
- Валидационные ошибки на русском языке

### ✅ Принцип XIX: Controllers
- Использовать HTTP статусы из starlette.status
- Никакой бизнес-логики в контроллерах
- Только вызовы CRUD или Service методов

### ✅ Принцип XVIII: Сервисный слой
- Использовать Pydantic-схемы для аргументов методов
- Передача данных в data-слой через `model_dump()`

**Результат**: ✅ Все gate'ы пройдены, нарушений нет

## Project Structure

### Documentation (this feature)

```text
specs/006-base-role-model/
├── spec.md              # Спецификация функции
├── plan.md              # Этот файл (выход /speckit.plan)
├── research.md          # Phase 0 выход (будет создан)
├── data-model.md        # Phase 1 выход (будет создан)
├── contracts/           # Phase 1 выход (будет создан)
│   └── roles.http       # HTTP контракты для API
└── tasks.md             # Phase 2 выход (выход /speckit.tasks - НЕ создается в /speckit.plan)
```

### Source Code (repository root)

```text
app/
├── api/
│   └── v1/
│       ├── controllers/
│       │   ├── users.py      # Существующий (добавить роль в схему ответа)
│       │   └── roles.py      # Новый: CRUD операции для ролевой модели
│       ├── dependencies.py   # Существующий (добавить get_current_user_with_role)
│       └── schemas/
│           ├── users.py      # Существующий (добавить role_id)
│           └── roles.py      # Новый: Pydantic схемы для Role
├── db/
│   ├── models/
│   │   ├── user.py           # Существующий (добавить role_id ForeignKey)
│   │   └── role.py           # Новый: модель Role
│   ├── crud/
│   │   ├── users.py          # Существующий
│   │   └── roles.py          # Новый: CRUD для Role
│   └── session.py            # Существующий
├── services/
│   ├── user_service.py       # Существующий (добавить логику роли)
│   ├── role_service.py       # Новый: бизнес-логика для ролей
│   └── current_user_service.py  # Существующий (добавить проверку роли)
└── config.py                 # Существующий (добавить DEFAULT_ADMIN_CREDENTIALS)

tests/
├── api/
│   └── v1/
│       └── controllers/
│           └── test_roles.py  # Новый: тесты для roles API
├── services/
│   └── test_role_service.py   # Новый: тесты для role service
└── conftest.py                 # Существующий (добавить role fixtures)

migrations/
└── versions/
    └── 2026_02_07_add_role_model.py  # Новая миграция: Role модель + связь User-Role
```

**Решение по структуре**: Single web API проект с существующей архитектурой Controller → Service → CRUD → DB. Добавляем новые файлы для Role сущности и расширяем существующие User-компоненты.

## Complexity Tracking

> **Не требуется** - никаких нарушений конституции, которые нужно оправдывать

---

## Phase 0: Research & Outline

### Исследовательские задачи

1. **SQLAlchemy 2.0 relationship**
   - Задача: Изучить лучшие практики для relationship в SQLAlchemy 2.0
   - Контекст: Связь User → Role (Many-to-One)
   - Вопросы: lazy loading, eager loading, cascade правила

2. **Alembic data migrations**
   - Задача: Изучить паттерны для миграций данных в Alembic
   - Контекст: Создание 3 ролей (user, manager, admin) + 1 пользователя (admin)
   - Вопросы: Как вставлять данные в migration, как обрабатывать повторные запуски

3. **Pydantic V2 Annotated types для Enums**
   - Задача: Изучить для Pydantic V2 с enum типами
   - Контекст: Валидация role_name (user/manager/admin)
   - Вопросы: Literal[str] vs Enum, сериализация/десериализация

4. **JWT токен payload расширение**
   - Задача: Изучить текущую реализацию JWT токенов
   - Контекст: Нужно ли добавлять role_id в JWT payload?
   - Вопросы: Производительность проверки роли из токена vs БД

5. **Dependency Injection паттерны в FastAPI**
   - Задача: Изучить паттерны для composition зависимостей
   - Контекст: get_current_user_with_role = get_current_user + проверка роли
   - Вопросы: Depends(Depends()), custom dependencies

### Выход Phase 0

Файл `research.md` с решениями по всем вышеуказанным задачам.

---

## Phase 1: Design & Contracts

### 1. Data Model (`data-model.md`)

**Сущность Role**
- Поля:
  - `id: int` (Primary Key)
  - `name: str` (уникальный, NOT NULL, "user"|"manager"|"admin")
  - `description: str|None` (опциональное описание)
  - `created_at: datetime`, `updated_at: datetime`
- Constraints:
  - `UNIQUE(name)`
  - 3 фиксированных значения для name

**Связь User → Role**
- Поля в User:
  - `role_id: int` (Foreign Key → Role.id, NOT NULL)
- Constraints:
  - `FOREIGN KEY (role_id) REFERENCES roles(id)`
  - `NOT NULL` (у каждого пользователя должна быть роль)
- Relationship:
  - `user.role: Role` (lazy='select' или lazy='joined')

**Справочные данные**
- Role(id=1, name="user")
- Role(id=2, name="manager")
- Role(id=3, name="admin")

### 2. API Contracts (`contracts/roles.http`)

**GET /api/v1/roles/** - Получить список всех ролей
**GET /api/v1/roles/{id}/** - Получить роль по ID
**GET /api/v1/users/me** - Обновить: добавить role_id в ответ
**POST /api/v1/users/** - Обновить: role_id может отсутствовать (по умолчанию user role)

### 3. Configuration Updates

**app/config.py**
- Добавить `DEFAULT_ADMIN_EMAIL`, `DEFAULT_ADMIN_PASSWORD`
- Или использовать существующие переменные окружения

### 4. Agent Context Update

Запустить `.specify/scripts/bash/update-agent-context.sh claude` для обновления контекста агента с новыми технологиями (если есть).

---

## Phase 2: Implementation Planning

> **Примечание**: Детальная разбивка на задачи будет создана командой `/speckit.tasks`

### Высокий уровень задач

1. **Создать модель Role** + миграцию
2. **Добавить role_id в User** + миграцию
3. **Создать CRUD для Role**
4. **Создать Service для Role**
5. **Обновить User Service** (автоматическая роль при регистрации)
6. **Обновить Current User Service** (проверка роли при каждом запросе)
7. **Создать API endpoints для Role**
8. **Написать тесты** (API, Service, CRUD)
9. **Обновить схемы** (User response, Role request/response)
10. **Создать миграцию данных** (3 роли + admin user)

### Определяющие факторы сложности

- **Data migration**: Вставка ролей + admin user в Alembic migration
- **ForeignKey constraint**: NOT NULL role_id в users таблице
- **Backward compatibility**: Существующие пользователи должны получить role_id
- **Role checking performance**: Оптимизация запросов к БД

---

## Следующие шаги

1. ✅ Constitution check пройден
2. ⏳ Выполнить Phase 0 Research → `research.md`
3. ⏳ Выполнить Phase 1 Design → `data-model.md`, `contracts/`
4. ⏳ Обновить agent context
5. ⏳ Перейти к `/speckit.tasks` для детальной разбивки
