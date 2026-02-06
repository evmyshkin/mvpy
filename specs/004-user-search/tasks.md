# Tasks: Поиск пользователей через API

**Feature Branch**: `004-user-search`
**Date**: 2025-02-06
**Status**: Ready for Implementation
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

Эта фича добавляет API endpoint для поиска пользователей с поддержкой двух сценариев:
1. **Поиск по email** (P1) - поиск конкретного пользователя
2. **Список всех пользователей** (P2) - получение всех пользователей

**Требования к тестированию**: Тесты обязательны согласно Конституции (Принцип VIII) и спецификации.

---

## Phase 1: Setup

**Цель**: Подготовить окружение для разработки

- [x] T001 Убедиться, что ветка `004-user-search` создана и активна
- [x] T002 Убедиться, что все зависимости установлены (`uv sync`)
- [x] T003 Убедиться, что тестовая БД PostgreSQL запущена (`make up` или локальная БД)

---

## Phase 2: Foundational

**Цель**: Реализовать общие компоненты, необходимые для обеих пользовательских историй

**Независимая проверка**: CRUD методы можно протестировать независимо от API endpoint

- [x] T004 Использовать существующую схему `UserUpdateResponse` для ответов поиска (id, email, first_name, last_name без password_hash)

- [x] T005 [P] Добавить метод `find_by_email_case_insensitive(session, email)` в класс `UsersCrud` в `app/db/crud/users.py`. Использовать `func.lower()` для case-insensitive поиска. Добавить docstring на русском.

- [x] T006 [P] Добавить метод `find_all_users(session)` в класс `UsersCrud` в `app/db/crud/users.py`. Использовать `select(User)` без фильтров. Добавить docstring на русском.

---

## Phase 3: User Story 1 - Поиск пользователя по email (Priority: P1)

**Цель**: Администратор может найти конкретного пользователя по email адресу

**Независимая проверка**: Можно протестировать GET запрос `/api/v1/users/?email=X` и проверить:
- Возвращает 200 и данные пользователя когда email существует
- Возвращает 404 когда email не существует
- Поиск работает без учета регистра (Test@Example.com = test@example.com)
- Пароль не возвращается в ответе

**Реализация**:

- [x] T007 [P] [US1] Добавить метод `search_user_by_email(session, email: str)` в класс `UserService` в `app/services/user_service.py`. Вызывать CRUD метод `find_by_email_case_insensitive`. Генерировать HTTPException 404 если пользователь не найден. Добавить docstring на русском.

- [x] T008 [P] [US1] Добавить тестовую фикстуру `valid_user_response` в `tests/conftest.py`. Возвращать `UserSearchResponse` с тестовыми данными (id, email, first_name, last_name).

- [x] T009 [US1] Добавить GET endpoint `/` в `app/api/v1/controllers/users.py`. Принимать опциональный query параметр `email: EmailStr | None`. Если email указан - вызывать сервисный метод `search_user_by_email`. Добавить docstring на русском.

- [x] T010 [US1] Добавить тест `test_search_user_by_email_success` в `tests/api/v1/controllers/test_users.py`. Создать пользователя через фикстуру, отправить GET запрос с email, проверить статус 200 и данные ответа (id, email, first_name, last_name).

- [x] T011 [US1] Добавить тест `test_search_user_by_email_case_insensitive` в `tests/api/v1/controllers/test_users.py`. Создать пользователя с lowercase email, искать с uppercase email, проверить что пользователь найден.

- [x] T012 [US1] Добавить тест `test_search_user_by_email_not_found` в `tests/api/v1/controllers/test_users.py`. Отправить GET запрос с несуществующим email, проверить статус 404 и русское сообщение об ошибке.

- [x] T013 [US1] Добавить тест `test_search_user_by_email_invalid_format` в `tests/api/v1/controllers/test_users.py`. Отправить GET запрос с невалидным email (без @), проверить статус 422.

---

## Phase 4: User Story 2 - Список всех пользователей (Priority: P2)

**Цель**: Администратор может получить список всех зарегистрированных пользователей

**Независимая проверка**: Можно протестировать GET запрос `/api/v1/users/` (без параметра email) и проверить:
- Возвращает 200 и массив пользователей
- Массив содержит всех пользователей из БД
- Пароли не возвращаются в ответе
- Пустой массив возвращается когда пользователей нет

**Реализация**:

- [x] T014 [P] [US2] Добавить метод `get_all_users(session)` в класс `UserService` в `app/services/user_service.py`. Вызывать CRUD метод `find_all_users`. Преобразовывать список User моделей в список UserSearchResponse. Добавить docstring на русском.

- [x] T015 [P] [US2] Обновить GET endpoint `/` в `app/api/v1/controllers/users.py`. Если параметр email не указан (None) - вызывать сервисный метод `get_all_users`. Тип возвращаемого значения: `UserSearchResponse | list[UserSearchResponse]`.

- [x] T016 [US2] Добавить тест `test_get_all_users_success` в `tests/api/v1/controllers/test_users.py`. Создать несколько пользователей через фикстуру, отправить GET запрос без email, проверить статус 200 и массив с пользователями.

- [x] T017 [US2] Добавить тест `test_get_all_users_empty_list` в `tests/api/v1/controllers/test_users.py`. Не создавать пользователей в тесте, отправить GET запрос без email, проверить статус 200 и пустой массив `[]`.

- [x] T018 [US2] Добавить тест `test_get_all_users_password_not_exposed` в `tests/api/v1/controllers/test_users.py`. Создать пользователя, отправить GET запрос без email, проверить что поле `password_hash` отсутствует в ответе.

- [x] T019 [US2] Добавить тест `test_search_user_by_email_vs_all_users` в `tests/api/v1/controllers/test_users.py`. Создать нескольких пользователей. Отправить GET с email (проверить один пользователь) и без email (проверить все пользователи). Убедиться что результаты различаются.

---

## Phase 5: Service Layer Tests

**Цель**: Покрытие тестами сервисного слоя

**Независимая проверка**: Сервисные методы можно протестировать независимо от API endpoint, используя mock сессию БД

- [x] T020 [P] Добавить тест `test_search_user_by_email_success` в `tests/services/test_user_service.py`. Использовать фикстуру `user_service`. Создать пользователя, вызвать метод сервиса, проверить что возвращается `UserSearchResponse` с корректными данными.

- [x] T021 [P] Добавить тест `test_search_user_by_email_not_found` в `tests/services/test_user_service.py`. Не создавать пользователя, вызвать метод сервиса, проверить что генерируется HTTPException 404.

- [x] T022 [P] Добавить тест `test_get_all_users_success` в `tests/services/test_user_service.py`. Создать несколько пользователей, вызвать метод сервиса, проверить что возвращается список `UserSearchResponse` с корректным количеством.

- [x] T023 [P] Добавить тест `test_get_all_users_empty` в `tests/services/test_user_service.py`. Не создавать пользователей, вызвать метод сервиса, проверить что возвращается пустой список.

---

## Phase 6: Polish & Quality Assurance

**Цель**: Обеспечить качество кода и полное покрытие тестами

**Независимая проверка**: Все проверки качества могут быть запущены независимо

- [x] T024 Запустить все тесты с покрытием: `make test` или `pytest --cov=app --cov-branch --cov-report=term-missing`. Убедиться что покрытие >85%.

- [x] T025 Запустить pre-commit hooks: `pre-commit run --all-files`. Убедиться что все проверки (Ruff, MyPy) проходят.

- [x] T026 Если есть проблемы от Ruff - исправить форматирование и ошибки (можно использовать `ruff format app/ tests/` и `ruff check --fix app/ tests/`).

- [x] T027 Если есть проблемы от MyPy - исправить типизацию в файлах с ошибками.

- [x] T028 Убедиться что все docstring-и написаны на русском языке (Google-style) для публичных методов в CRUD, Service и Controller слоях.

- [x] T029 Убедиться что все сообщения об ошибках локализованы на русский язык (HTTPException detail, Pydantic валидация).

- [ ] T030 Протестировать endpoint вручную через Swagger UI: запустить сервер (`make dev`), открыть `http://localhost:8000/docs`, протестировать все сценарии (успешный поиск, не найдено, невалидный email, список всех пользователей).

- [x] T031 Убедиться что код соответствует всем принципам Конституции ( см. `plan.md` Constitution Check).

---

## Dependencies

### Граф зависимостей

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational: Schemas + CRUD)
    ↓
┌──────────────────────────────────────┐
│                                      │
Phase 3 (US1: Search by email)    Phase 4 (US2: List all users)
│                                      │
└──────────────────────────────────────┘
    ↓
Phase 5 (Service Tests)
    ↓
Phase 6 (Polish & QA)
```

### Порядок реализации

1. **Setup** (Phase 1) - подготовка окружения
2. **Foundational** (Phase 2) - общие компоненты (Schemas + CRUD)
3. **US1** (Phase 3) - поиск по email (P1) - **MVP scope**
4. **US2** (Phase 4) - список всех пользователей (P2)
5. **Service Tests** (Phase 5) - тесты сервисного слоя
6. **Polish** (Phase 6) - качество и QA

**Примечание**: User Story 1 и User Story 2 зависят от foundational компонентов, но могут быть реализованы параллельно после Phase 2.

---

## Parallel Execution Examples

### Параллельное выполнение в Phase 2 (Foundational)

```bash
# T005 и T006 могут выполняться параллельно (разные файлы, нет зависимостей)
Terminal 1: Реализовать T005 (find_by_email_case_insensitive)
Terminal 2: Реализовать T006 (find_all_users)
```

### Параллельное выполнение в Phase 3 (US1)

```bash
# T007 и T008 могут выполняться параллельно
Terminal 1: Реализовать T007 (сервисный метод)
Terminal 2: Реализовать T008 (тестовая фикстура)

# T010-T013 могут выполняться параллельно (разные тесты)
Terminal 1: T010 + T011 (тесты на успех)
Terminal 2: T012 + T013 (тесты на ошибки)
```

### Параллельное выполнение в Phase 4 (US2)

```bash
# T014 и T015 могут выполняться параллельно
Terminal 1: Реализовать T014 (сервисный метод)
Terminal 2: Реализовать T015 (update controller)

# T016-T019 могут выполняться параллельно (разные тесты)
Terminal 1: T016 + T017 (тесты на успех и пустой список)
Terminal 2: T018 + T019 (тесты на безопасность и различия)
```

### Параллельное выполнение в Phase 5 (Service Tests)

```bash
# T020-T023 могут выполняться параллельно (разные тесты)
Terminal 1: T020 + T021 (тесты search_user_by_email)
Terminal 2: T022 + T023 (тесты get_all_users)
```

---

## Implementation Strategy

### MVP (Minimum Viable Product)

**Scope**: Phase 1 + Phase 2 + Phase 3 (US1)

**Что включено**:
- Setup (T001-T003)
- Foundational компоненты (T004-T006)
- Поиск пользователя по email (T007-T013)

**Критерий завершения**: Администратор может найти пользователя по email через API endpoint

**Время**: Ожидается 2-3 часа для реализации

### Полная реализация (Full Implementation)

**Scope**: Все фазы (T001-T031)

**Что включено**:
- MVP + Список всех пользователей (T014-T019)
- Тесты сервисного слоя (T020-T023)
- Quality assurance (T024-T031)

**Критерий завершения**: Все требования из spec.md выполнены, покрытие >85%

**Время**: Ожидается 4-5 часов для полной реализации

### Инкрементальная доставка

1. **Sprint 1**: MVP (Phase 1-3) - Поиск по email
2. **Sprint 2**: US2 (Phase 4) - Список всех пользователей
3. **Sprint 3**: QA (Phase 5-6) - Тесты и качество

---

## Task Summary

| Phase | Description | Task Count | Parallelizable |
|-------|-------------|------------|----------------|
| Phase 1 | Setup | 3 | 0 |
| Phase 2 | Foundational | 3 | 2 (T005, T006) |
| Phase 3 | US1 - Search by email | 7 | 2 (T007, T008) |
| Phase 4 | US2 - List all users | 6 | 2 (T014, T015) |
| Phase 5 | Service tests | 4 | 4 (T020-T023) |
| Phase 6 | Polish & QA | 8 | 0 |
| **Total** | | **31** | **10 (32%)** |

---

## Format Validation

✅ Все задачи следуют обязательному формату: `- [ ] [TaskID] [P?] [Story?] Description with file path`

✅ Setup phase: Без метки [Story]
✅ Foundational phase: Без метки [Story]
✅ User Story phases: С меткой [US1] или [US2]
✅ Polish phase: Без метки [Story]

✅ Все задачи содержат конкретные пути к файлам

✅ Параллельные задачи отмечены меткой [P]

---

## Next Steps

1. **Начать имплементацию**:
   ```bash
   /speckit.implement Phase 1
   ```

2. **Или реализовать конкретную задачу**:
   ```bash
   /speckit.implement T004
   ```

3. **Или реализовать MVP целиком**:
   ```bash
   /speckit.implement Phase 1, Phase 2, Phase 3
   ```

---

**Готовность к имплементации**: ✅ Все задачи детализированы и могут быть выполнены LLM независимо без дополнительного контекста.
