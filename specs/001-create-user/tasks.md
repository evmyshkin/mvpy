# Implementation Tasks: Создание пользователя через API

**Branch**: `001-create-user` | **Date**: 2026-02-05
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Summary

Этот документ содержит задачи для реализации API создания пользователя с хешированием паролей. Задачи организованы по user stories для независимой реализации и тестирования.

**User Stories**:
- **US1 (P1)**: Успешное создание пользователя - базовый endpoint с валидацией
- **US2 (P2)**: Валидация данных пользователя - детальная валидация полей

**Total Tasks**: 22
**Tasks per story**: US1: 14 tasks, US2: 6 tasks, Setup: 2 tasks

---

## Phase 1: Setup

### Goal
Настроить проект и добавить необходимые зависимости для хеширования паролей.

### Tasks

- [x] T001 Добавить зависимость passlib[bcrypt] в pyproject.toml
- [x] T002 Запустить uv sync для установки новых зависимостей

---

## Phase 2: Foundational

### Goal
Создать базовые компоненты (модель БД, миграцию), которые требуются для обеих user stories.

### Tasks

- [x] T003 Создать SQLAlchemy модель User в app/db/models/user.py с полями: id, email (unique), first_name, last_name, password_hash, created_at, updated_at
- [x] T004 Добавить импорт User в app/db/models/__init__.py для обнаружения Alembic
- [x] T005 Создать Alembic миграцию для таблицы users с уникальным constraint на email
- [x] T006 Применить миграцию к БД: alembic upgrade head

---

## Phase 3: User Story 1 - Успешное создание пользователя (P1)

### Goal
Реализовать базовый endpoint для создания пользователя с хешированием пароля, проверкой уникальности email и возвратом статуса 201.

### Independent Test Criteria
- ✅ POST /api/v1/users/ с валидными данными возвращает статус 201
- ✅ Ответ содержит id, email, first_name, last_name (без пароля)
- ✅ Дубликат email возвращает статус 409
- ✅ Пароль сохранён в БД в захешированном виде

### Tasks

#### Pydantic Schemas
- [ ] T007 [P] [US1] Создать UserCreateRequest в app/api/v1/schemas/users.py с полями: email (EmailStr), first_name, last_name, password
- [ ] T008 [P] [US1] Создать UserCreateResponse в app/api/v1/schemas/users.py с полями: id, email, first_name, last_name, created_at, updated_at

#### CRUD Layer
- [ ] T009 [P] [US1] Создать UsersCrud в app/db/crud/users.py, который наследует BaseCrud[User]
- [ ] T010 [P] [US1] Добавить метод find_by_email в UsersCrud для поиска пользователя по email
- [ ] T011 [P] [US1] Добавить метод email_exists в UsersCrud для проверки существования email

#### Service Layer
- [ ] T012 [US1] Создать функцию hash_password в app/services/user_service.py для хеширования пароля через passlib bcrypt
- [ ] T013 [US1] Создать UserService в app/services/user_service.py, который наследует BaseService с UsersCrud
- [ ] T014 [US1] Добавить метод create_user в UserService с логикой: проверка email_exists, хеширование пароля, вызов crud.add_one, обработка IntegrityError

#### Controller Layer
- [ ] T015 [US1] Создать роутер users в app/api/v1/controllers/users.py с POST endpoint на /users/
- [ ] T016 [US1] Добавить обработчик запроса с Depends(connector.get_session) для асинхронной сессии БД
- [ ] T017 [US1] Реализовать логику endpoint: валидация UserCreateRequest, вызов user_service.create_user, возврат UserCreateResponse со статусом 201
- [ ] T018 [US1] Добавить Location header с путём к созданному пользователю

#### Router Integration
- [ ] T019 [US1] Подключить users роутер в app/api/v1/router.py
- [ ] T020 [US1] Проверить что главный роутер в app/api/router.py включает v1 роутер

#### Tests
- [ ] T021 [P] [US1] Создать test_users.py в tests/api/v1/controllers/ с тестами: успешное создание, дубликат email, захешированный пароль в БД
- [ ] T022 [US1] Запустить make test и убедиться что все тесты проходят

---

## Phase 4: User Story 2 - Валидация данных пользователя (P2)

### Goal
Добавить детальную валидацию полей: имя/фамилия (только буквы и тире), сложность пароля, длина полей.

### Independent Test Criteria
- ✅ Имя/фамилия с цифрами возвращает 422
- ✅ Пароль короче 8 символов возвращает 422
- ✅ Пароль без заглавной/строчной буквы или цифры возвращает 422
- ✅ Понятные сообщения об ошибках для всех случаев

### Tasks

#### Pydantic Validators
- [x] T023 [P] [US2] Добавить field_validator для first_name и last_name в UserCreateRequest с regex `^[А-Яа-яA-Za-z\-]+$` и проверкой длины до 100 символов
- [x] T024 [P] [US2] Добавить field_validator для password length в UserCreateRequest (минимум 8, максимум 100 символов)
- [x] T025 [P] [US2] Добавить field_validator для password complexity в UserCreateRequest (минимум 1 заглавная, 1 строчная, 1 цифра)

#### Tests
- [x] T026 [P] [US2] Добавить тесты для валидации имени/фамилии в test_users.py (цифры, спецсимволы, длина)
- [x] T027 [P] [US2] Добавить тесты для валидации пароля в test_users.py (длина, отсутствие заглавных/строчных/цифр)
- [x] T028 [US2] Запустить make test и убедиться что все тесты проходят

---

## Phase 5: Polish & Cross-Cutting Concerns

### Goal
Финальная проверка качества кода, документация и подготовка к production.

### Tasks

- [x] T029 Запустить pre-commit run --all-files и исправить все ошибки
- [x] T030 Запустить ruff format app/ tests/ для форматирования кода
- [x] T031 Запустить mypy app/ для проверки типов
- [x] T032 Добавить Google-style docstrings на русском во все публичные классы и методы
- [x] T033 Проверить автогенерируемую документацию на http://localhost:8000/docs
- [x] T034 Убедиться что покрытие кода тестами соответствует требованиям (--cov-branch)

---

## Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
    ├─→ Phase 3 (US1) [блокирует US2]
    │       ↓
    └─→ Phase 4 (US2)
            ↓
        Phase 5 (Polish)
```

**Blocking Dependencies**:
- Phase 2 (Foundational) ДОЛЖЕН завершиться перед Phase 3 (US1)
- Phase 3 (US1) ДОЛЖЕН завершиться перед Phase 4 (US2)

**Rationale**:
- Без модели User и миграции нельзя реализовать CRUD, Service и Controller
- US1 создаёт базовую инфраструктуру (endpoint), которую US2 расширяет валидацией

---

## Parallel Execution Opportunities

### Phase 3 (US1) - Parallel Tasks
```bash
# Могут выполняться параллельно (разные файлы):
T007, T008  # Pydantic schemas (разные классы в одном файле - последовательные)
T009, T010, T011  # CRUD layer (один файл - последовательные)
T021  # Tests (независимо от реализации)

# Последовательная цепочка:
T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020
```

### Phase 4 (US2) - Parallel Tasks
```bash
# Могут выполняться параллельно (разные валидаторы):
T023, T024, T025  # Pydantic validators (один файл - последовательные)
T026, T027  # Tests (разные тесты - могут быть параллельными)

# Последовательная цепочка:
T023 → T024 → T025 → T026 → T027 → T028
```

---

## Implementation Strategy

### MVP (Minimum Viable Product)
**Scope**: Phase 1 + Phase 2 + Phase 3 (US1 только)

**MVP Tasks**: T001-T022 (22 tasks)

**MVP Deliverables**:
- ✅ POST /api/v1/users/ endpoint
- ✅ Создание пользователя с валидными данными
- ✅ Проверка уникальности email
- ✅ Хеширование паролей
- ✅ Базовые тесты

### Incremental Delivery
**Iteration 1**: MVP (Phase 1-3) - работающий endpoint для создания пользователя
**Iteration 2**: US2 (Phase 4) - детальная валидация данных
**Iteration 3**: Polish (Phase 5) - качество кода и документация

### Risk Mitigation
- **Early Integration**: T021 (тесты) создаются параллельно с реализацией для раннего обнаружения проблем
- **Incremental Validation**: После каждой фазы запускать `make test` для проверки работоспособности
- **Constitution Compliance**: T029-T031 проверяют соответствие стандартам качества кода

---

## Format Validation

✅ **ALL tasks follow the checklist format**:
- Checkbox: `- [ ]` present
- Task ID: T001-T034 sequential
- [P] marker: Applied to parallelizable tasks
- [Story] label: [US1], [US2] applied to user story phase tasks
- Description: Clear action with file path

✅ **Format examples**:
- Setup: `- [ ] T001 Добавить зависимость passlib[bcrypt] в pyproject.toml`
- Foundational: `- [ ] T003 Создать SQLAlchemy модель User в app/db/models/user.py`
- US1 Parallel: `- [ ] T007 [P] [US1] Создать UserCreateRequest в app/api/v1/schemas/users.py`
- US1 Sequential: `- [ ] T014 [US1] Добавить метод create_user в UserService`
- US2 Parallel: `- [ ] T023 [P] [US2] Добавить field_validator для first_name и last_name`

---

## References

- **Spec**: [spec.md](./spec.md) - User stories и функциональные требования
- **Plan**: [plan.md](./plan.md) - Технический стек и архитектура
- **Data Model**: [data-model.md](./data-model.md) - Схема БД и Pydantic модели
- **Research**: [research.md](./research.md) - Технические решения
- **Quickstart**: [quickstart.md](./quickstart.md) - Примеры использования