# Implementation Tasks: Update User via API

**Feature**: 002-update-user
**Branch**: `002-update-user`
**Generated**: 2025-02-05
**Total Tasks**: 13

## Overview

Этот документ содержит разбивку задач для имплементации API-эндпоинта обновления пользователя. Задачи организованы по user story с приоритетами из спецификации. Тестирование является обязательным согласно конституции проекта.

## User Stories

- **User Story 1 (P1)**: Обновление информации о пользователе через API
  - Цель: Позволить клиентам API обновлять поля пользователей (first_name, last_name, password, email)
  - Independent Test: Создать пользователя, обновить его через PUT /api/v1/users/{id}, проверить изменения

---

## Phase 1: Setup

**Цель**: Подготовить окружение и убедиться, что все зависимости установлены

- [X] T001 Убедиться, что все зависимости установлены через `uv sync`
- [X] T002 Убедиться, что PostgreSQL запущен и миграции применены через `alembic upgrade head`
- [X] T003 Убедиться, что существующая модель User в `app/db/models/user.py` не требует изменений

---

## Phase 2: Foundational

**Цель**: Создать базовые компоненты, необходимые для User Story 1

- [X] T004 Создать переиспользуемые валидаторы имён в `app/api/v1/schemas/users.py`
  - Вынести логику валидации из UserCreateRequest в отдельные функции
  - Функция `validate_name_field()` с regex для букв кириллицы/латиницы и дефисов
  - Все сообщения об ошибках на русском языке

- [X] T005 Создать переиспользуемые валидаторы пароля в `app/api/v1/schemas/users.py`
  - Вынести логику валидации из UserCreateRequest в отдельные функции
  - Функция `validate_password_length()` (8-100 символов)
  - Функция `validate_password_complexity()` (1 заглавная, 1 строчная, 1 цифра)
  - Все сообщения об ошибках на русском языке

---

## Phase 3: User Story 1 - Update User via API (Priority: P1)

**Цель**: Реализовать PUT /api/v1/users/{user_id} эндпоинт

**Independent Test Criteria**:
- Создать пользователя через POST /api/v1/users/
- Обновить пользователя через PUT /api/v1/users/{id} с различными комбинациями полей
- Проверить, что изменения сохранены в БД
- Проверить все сценарии ошибок (404, 400, 422)

**Implementation Tasks**:

- [X] T006 [P] [US1] Создать Pydantic схему UserUpdateRequest в `app/api/v1/schemas/users.py`
  - Все поля опциональны (Optional[str] | None)
  - Поле `email: EmailStr | None`
  - Поле `first_name: str | None`
  - Поле `last_name: str | None`
  - Поле `password: str | None`
  - Добавить field_validator для first_name и last_name с использованием переиспользуемых валидаторов
  - Добавить field_validator для password с использованием переиспользуемых валидаторов
  - Все сообщения об ошибках на русском языке

- [X] T007 [P] [US1] Создать Pydantic схему UserUpdateResponse в `app/api/v1/schemas/users.py`
  - Обязательные поля: id, email, first_name, last_name
  - Пароль не возвращается в ответе

- [X] T008 [US1] Создать метод update_user() в UserService в `app/services/user_service.py`
  - Принимать параметры: session, user_id, email (optional), first_name (optional), last_name (optional), password (optional)
  - Проверить существование пользователя через UsersCrud.find_one_or_none(id=user_id)
  - Если пользователь не найден: raise HTTPException(status_code=404, detail='Пользователь не найден')
  - Если email предоставлен и отличается от текущего: проверить email uniqueness через UsersCrud.email_exists()
  - Если email уже занят: raise HTTPException(status_code=400, detail='Пользователь с таким email уже существует')
  - Если password предоставлен: захешировать через hash_password()
  - Собрать values dict только для предоставлённых полей
  - Обновить пользователя через UsersCrud.update_one_or_none(filter_by={'id': user_id}, values=values)
  - Если update_one_or_none вернул None: raise HTTPException(status_code=404, detail='Пользователь не найден')
  - Маппить User → UserUpdateResponse
  - Добавить Google-style docstring на русском языке

- [X] T009 [US1] Создать PUT эндпоинт в `app/api/v1/controllers/users.py`
  - Path: `/{user_id}` где user_id: int
  - Метод: `async def update_user(user_id: int, user_data: UserUpdateRequest, db: AsyncSession = Depends(connector.get_session))`
  - Вызвать UserService.update_user() с передачей всех полей из user_data
  - response_model=UserUpdateResponse, status_code=200
  - Добавить Google-style docstring на русском языке

- [X] T010 [P] [US1] Создать фикстуры для тестов в `tests/conftest.py`
  - Добавить фикстуру `update_user_request(faker: Faker) -> UserUpdateRequest` с валидными тестовыми данными
  - Добавить фикстуру `existing_user(db_session: AsyncSession) -> User` для создания пользователя перед тестами update
  - Использовать Pydantic модели для создания тестовых данных

- [X] T011 [P] [US1] Создать тесты для UserService в `tests/services/test_user_service.py`
  - `test_update_user_success()` - успешное обновление всех полей
  - `test_update_user_partial()` - частичное обновление одного поля
  - `test_update_user_not_found()` - несуществующий user_id (404)
  - `test_update_user_duplicate_email()` - duplicate email (400)
  - `test_update_user_same_email()` - обновление с тем же email (успех)
  - `test_update_user_password_hashed()` - проверка хеширования пароля

- [X] T012 [P] [US1] Создать тесты для API endpoint в `tests/api/v1/controllers/test_users.py`
  - `test_update_user_success()` - успешное обновление (200)
  - `test_update_user_partial()` - частичное обновление одного поля (200)
  - `test_update_user_not_found()` - несуществующий user_id (404)
  - `test_update_user_duplicate_email()` - duplicate email (400)
  - `test_update_user_invalid_email()` - невалидный формат email (422)
  - `test_update_user_invalid_name()` - имя с цифрами (422)
  - `test_update_user_weak_password()` - слабый пароль (422)
  - `test_update_user_all_errors()` - множественные ошибки валидации (422)
  - Использовать async_client и Pydantic модели

- [X] T013 [US1] Запустить все тесты и убедиться, что покрытие ветвлений полное
  - Выполнить `pytest --cov=app --cov-branch --cov-report=term-missing`
  - Убедиться, что все тесты проходят
  - Проверить, что покрытие новых функций и методов близко к 100%

---

## Dependencies

### Graph

```text
Phase 1 (Setup)
  ↓
Phase 2 (Foundational)
  ↓
Phase 3 (User Story 1)
  ├─ T006 [UserUpdateRequest] ──┬─→ T008 [UserService]
  ├─ T007 [UserUpdateResponse] ──┤          ↓
  └─ T004-T005 [Validators]     ──┴─→ T009 [Controller] ──→ T010-T013 [Tests]
```

### Story Completion Order

1. **Phase 1**: Setup (T001-T003) - подготовить окружение
2. **Phase 2**: Foundational (T004-T005) - создать переиспользуемые валидаторы
3. **Phase 3**: User Story 1 (T006-T013) - реализовать PUT endpoint и тесты

**Story Independence**: User Story 1 полностью независима и может быть имплементирована и протестирована отдельно.

---

## Parallel Execution Opportunities

### Phase 1 (Setup)
- **Нет параллельных задач**: все задачи должны выполняться последовательно для проверки окружения

### Phase 2 (Foundational)
- **P**: T004 и T005 могут выполняться параллельно (разные файлы, независимые функции)

### Phase 3 (User Story 1)
- **P**: T006, T007, T010 могут выполняться параллельно после Phase 2 (разные файлы)
- **P**: T011 и T012 могут выполняться параллельно после T009 (разные тестовые файлы)

### Example Parallel Execution

```bash
# После завершения Phase 2, выполнить параллельно:
Terminal 1: T006 - UserUpdateRequest schema
Terminal 2: T007 - UserUpdateResponse schema
Terminal 3: T010 - Test fixtures

# После завершения T008-T009, выполнить параллельно:
Terminal 1: T011 - UserService tests
Terminal 2: T012 - API endpoint tests
```

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1)**

После завершения всех задач Phase 3:
- ✅ PUT /api/v1/users/{user_id} полностью функционален
- ✅ Поддержка всех сценариев из спецификации (успех, ошибки, частичные обновления)
- ✅ Полное покрытие тестами
- ✅ Все ошибки локализованы на русский язык
- ✅ Фича готова к продакшену

### Incremental Delivery

1. **После Phase 2**: Переиспользуемые валидаторы готовы для будущего переиспользования
2. **После Phase 3**: Полностью готовый PUT endpoint с тестами

**Рекомендация**: Выполнять задачи последовательно по фазам для раннего обнаружения проблем.

---

## Quality Gates

### После Phase 1 (Setup)
- [X] Все зависимости установлены
- [X] PostgreSQL запущен и миграции применены
- [X] Существующие тесты проходят (`make test`)

### После Phase 2 (Foundational)
- [X] Переиспользуемые валидаторы созданы
- [X] Существующие UserCreateRequest схемы обновлены для использования новых валидаторов
- [X] Все тесты всё ещё проходят

### После Phase 3 (User Story 1)
- [X] Все новые тесты проходят (`pytest tests/ -k update`)
- [X] Покрытие ветвлений ≥ 90% для нового кода (100% для API схем, контроллеров, CRUD, models)
- [X] Pre-commit hooks проходят (`pre-commit run --all-files`)
- [X] Ручное тестирование API подтверждает все сценарии из спецификации
- [X] Все ошибки на русском языке

---

## Notes

- **Локализация ошибок**: Все сообщения об ошибках в Pydantic валидаторах и HTTPException должны быть на русском языке согласно принципу XI конституции
- **Переиспользование**: Валидаторы должны быть переиспользуемы между UserCreateRequest и UserUpdateRequest
- **Хеширование паролей**: Использовать существующую функцию hash_password() из user_service.py
- **BaseCrud**: Использовать существующий метод update_one_or_none() без изменений
- **Конституция**: Все имплементации должны соответствовать принципам из constitution.md
- **TDD**: Тесты пишутся одновременно с кодом или сразу после (принцип VIII)
