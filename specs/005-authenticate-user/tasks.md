# Задачи имплементации: Аутентификация и авторизация пользователей

**Ветка**: `005-authenticate-user`
**Дата**: 2025-02-06
**Спецификация**: [spec.md](./spec.md)
**План**: [plan.md](./plan.md)

## Обзор

Этот документ содержит задачи для реализации системы аутентификации и авторизации пользователей на основе JWT токенов. Задачи организованы по пользовательским историям (user stories) в порядке приоритета (P1 → P2 → P3), что позволяет независимо реализовать и тестировать каждую историю.

**Всего задач**: 37
**User Stories**: 3 (P1: Аутентификация, P2: Выход из системы, P3: Авторизация)
**Параллельных задач**: 12 (можно выполнять параллельно в пределах одной фазы)

## Стратегия имплементации

### MVP Scope (Mинимально жизнеспособный продукт)

**Рекомендуемый MVP**: User Story 1 (Аутентификация) + Фазы Setup и Foundational

Это позволяет:
- Пользователям входить в систему с email и паролем
- Получать JWT токены для дальнейшего использования
- Базовая безопасность без logout и авторизации

**MVP включает задачи**: T001-T025 (Setup + Foundational + US1)

### Инкрементальная доставка

1. **Sprint 1**: US1 (Аутентификация) - Пользователи могут логиниться и получать токены
2. **Sprint 2**: US2 (Выход из системы) - Пользователи могут логаутиться
3. **Sprint 3**: US3 (Авторизация) - Защита всех эндпоинтов

### Параллельное выполнение

Внутри каждой фазы задачи, помеченные `[P]`, можно выполнять параллельно, так как они работают с разными файлами и не зависят от незавершённых задач.

---

## Phase 1: Setup (Настройка проекта)

**Цель**: Добавить зависимости и настроить конфигурацию JWT.

**Задачи**:

- [X] T001 Установить зависимость python-jose[cryptography] в pyproject.toml
- [X] T002 [P] Создать Enum для сообщений об ошибках аутентификации в app/api/utils/enums/auth.py
- [X] T003 [P] Добавить JWT конфигурацию в app/config.py (JWTConfig с Pydantic Settings)

**Критерий завершения**: Зависимость установлена, конфигурация JWT добавлена, enum'ы для сообщений созданы.

---

## Phase 2: Foundational (Фундаментальные компоненты)

**Цель**: Создать базовые компоненты, необходимые для всех user stories (модель BlacklistedToken, CRUD, миграции, фикстуры для тестов).

**Задачи**:

- [X] T004 Создать модель BlacklistedToken в app/db/models/blacklisted_token.py
- [X] T005 [P] Создать CRUD для BlacklistedToken в app/db/crud/blacklisted_tokens.py
- [X] T006 Обновить app/db/models/__init__.py для импорта BlacklistedToken
- [X] T007 Создать миграцию Alembic 005_add_blacklisted_tokens.py
- [X] T008 Применить миграцию к БД (alembic upgrade head)
- [X] T009 [P] Создать базовые фикстуры для auth токенов в tests/conftest.py
- [X] T010 [P] Создать helper функции для генерации JWT токенов в тестах (tests/conftest.py)

**Критерий завершения**: Таблица blacklisted_tokens создана в БД, CRUD готов, тестовые фикстуры для токенов добавлены.

**Зависимости**: Все задачи этой фазы должны быть завершены до начала любой user story.

---

## Phase 3: User Story 1 - Аутентификация (Priority P1)

**Цель**: Пользователи могут аутентифицироваться по email и паролю и получать JWT токены.

**Независимая проверка**: Можно полностью протестировать: POST /api/v1/auth/login с валидными учетными данными → получить токен, с неверными → получить ошибку 401.

**Сценарии приемки**:
1. ✅ Валидные email + password → токен (200 OK)
2. ✅ Email не существует → ошибка "Неверный email или пароль" (401)
3. ✅ Неверный пароль → ошибка "Неверный email или пароль" (401)
4. ✅ Деактивированный пользователь → ошибка "Учётная запись неактивна" (401)
5. ✅ Токен содержит user_id, is_active, exp, iat, jti

**Задачи**:

### Модели и Сервисы

- [X] T011 [P] [US1] Создать Pydantic схемы AuthRequest и AuthResponse в app/api/v1/schemas/auth.py
- [X] T012 [US1] Создать AuthService в app/services/auth_service.py (метод authenticate)
- [X] T013 [P] [US1] Создать Pydantic схему LogoutResponse в app/api/v1/schemas/auth.py

### Контроллеры

- [X] T014 [US1] Создать auth контроллер с эндпоинтом POST /auth/login в app/api/v1/controllers/auth.py
- [X] T015 [US1] Реализовать бизнес-логику аутентификации в AuthService.authenticate (проверка email, password, is_active)
- [X] T016 [US1] Реализовать генерацию JWT токена в AuthService (создаёт токен с user_id, is_active, exp, iat, jti)
- [X] T017 [US1] Добавить обработку ошибок: универсальное сообщение "Неверный email или пароль" для неверных учетных данных
- [X] T018 [US1] Добавить обработку ошибки: сообщение "Учётная запись неактивна" для is_active=False

### Роутинг

- [X] T019 [US1] Создать auth роутер в app/api/v1/router.py и включить его в главный роутер

### Тесты

- [X] T020 [P] [US1] Создать тесты для AuthService в tests/services/test_auth_service.py (authenticate_success, authenticate_user_not_found, authenticate_wrong_password, authenticate_inactive_user)
- [X] T021 [P] [US1] Создать тесты для auth эндпоинта в tests/api/v1/controllers/test_auth.py (test_login_success, test_login_user_not_found, test_login_wrong_password, test_login_inactive_user, test_login_validation_error)

### Интеграция

- [X] T022 [US1] Запустить тесты: pytest tests/services/test_auth_service.py tests/api/v1/controllers/test_auth.py -v
- [X] T023 [US1] Убедиться, что все тесты проходят и покрытие > 90%

**Критерий завершения US1**: POST /auth/login работает, возвращает JWT токен для валидных учетных данных, возвращает соответствующие ошибки для неверных, все тесты проходят.

**Зависимости**: Требует Phase 1 (Setup) и Phase 2 (Foundational).

---

## Phase 4: User Story 2 - Выход из системы (Priority P2)

**Цель**: Пользователи могут выходить из системы, их токены аннулируются.

**Независимая проверка**: Можно полностью протестировать: Аутентифицироваться → получить токен, вызвать logout → токен добавляется в blacklist, попытка использовать токен → ошибка 401.

**Сценарии приемки**:
1. ✅ Валидный токен + POST /auth/logout → токен в blacklist, подтверждение logout
2. ✅ Отозванный токен + защищённый эндпоинт → ошибка "Токен отозван" (401)
3. ✅ Неаутентифицированный запрос + logout → ошибка "Отсутствует токен авторизации" (401)

**Задачи**:

### Сервисы

- [X] T024 [US2] Добавить метод logout в AuthService (добавляет токен в blacklist через BlacklistedTokenCrud)

### Контроллеры

- [X] T025 [US2] Добавить эндпоинт POST /auth/logout в app/api/v1/controllers/auth.py (использует AuthService.logout)
- [X] T026 [US2] Добавить проверку авторизации для logout (требуется валидный токен)

### Dependency Injection

- [X] T027 [P] [US2] Создать dependency get_current_user в app/api/v1/controllers/auth.py (извлекает пользователя из токена)
- [X] T028 [P] [US2] Создать dependency oauth2_scheme (FastAPI SecurityScheme для Bearer токена)

### Тесты

- [X] T029 [P] [US2] Добавить тесты для logout в tests/services/test_auth_service.py (test_logout_success, test_logout_token_already_blacklisted)
- [X] T030 [P] [US2] Добавить тесты для logout эндпоинта в tests/api/v1/controllers/test_auth.py (test_logout_success, test_logout_no_token, test_logout_invalid_token, test_logout_expired_token, test_logout_blacklisted_token)

### Интеграция

- [X] T031 [US2] Запустить все тесты: pytest tests/services/test_auth_service.py tests/api/v1/controllers/test_auth.py -v
- [X] T032 [US2] Убедиться, что все тесты проходят и покрытие > 90%

**Критерий завершения US2**: POST /auth/logout работает, токены добавляются в blacklist, отозванные токены отклоняются, все тесты проходят.

**Зависимости**: Требует Phase 1, Phase 2 и Phase 3 (US1 - нужен рабочий login для тестирования logout).

---

## Phase 5: User Story 3 - Базовая авторизация (Priority P3)

**Цель**: Защитить все эндпоинты кроме auth и register, проверять токен и is_active при каждом запросе.

**Независимая проверка**: Можно полностью протестировать: Валидный токен + защищённый эндпоинт → доступ разрешён, нет токена/невалидный токен/is_active=False → доступ запрещён, публичные эндпоинты (auth, register) доступны без токена.

**Сценарии приемки**:
1. ✅ Валидный токен (is_active=True) + защищённый эндпоинт → доступ разрешён (200 OK)
2. ✅ Нет токена + защищённый эндпоинт → ошибка "Отсутствует токен авторизации" (401)
3. ✅ Токен с is_active=False + защищённый эндпоинт → ошибка "Учётная запись неактивна" (401)
4. ✅ Публичные эндпоинты (POST /users/, POST /auth/login) доступны без токена

**Задачи**:

### Сервисы

^- [X] T033 [US3] Обновить get_current_user dependency: проверять токен в blacklist, проверять is_active из токена, возвращать User или raise HTTPException

### Контроллеры (защита эндпоинтов)

^- [X] T034 [P] [US3] Добавить get_current_user dependency к GET /api/v1/users/{user_id} (существующий эндпоинт)
^- [X] T035 [P] [US3] Добавить get_current_user dependency к PUT /api/v1/users/{user_id} (существующий эндпоинт)
^- [X] T036 [P] [US3] Добавить get_current_user dependency к DELETE /api/v1/users/{user_id} (существующий эндпоинт)
^- [X] T037 [P] [US3] Добавить get_current_user dependency к GET /api/v1/users/ (существующий эндпоинт)

### Тесты

^- [X] T038 [P] [US3] Создать тесты для get_current_user dependency в tests/api/v1/controllers/test_auth.py (test_get_current_user_success, test_get_current_user_no_token, test_get_current_user_invalid_token, test_get_current_user_expired_token, test_get_current_user_blacklisted_token, test_get_current_user_inactive_user)
^- [X] T039 [P] [US3] Создать тесты для защищённых эндпоинтов в tests/api/v1/controllers/test_users.py (test_get_user_requires_auth, test_update_user_requires_auth, test_delete_user_requires_auth, test_list_users_requires_auth, test_public_endpoints_accessible_without_auth)

### Интеграция

- [ ] T040 [US3] Запустить все тесты: pytest tests/ -v
- [ ] T041 [US3] Убедиться, что все тесты проходят и покрытие > 90%

**Критерий завершения US3**: Все защищённые эндпоинты требуют валидный токен, публичные эндпоинты доступны без токена, is_active проверяется, все тесты проходят.

**Зависимости**: Требует Phase 1, Phase 2, Phase 3 (US1) и Phase 4 (US2 - нужен get_current_user).

---

## Phase 6: Polish & Cross-Cutting Concerns (Финальная доработка)

**Цель**: Финальная полировка, документация, проверка качества кода.

**Задачи**:

- [ ] T042 Обновить .env.example с JWT__SECRET_KEY и JWT__ACCESS_TOKEN_EXPIRE_MINUTES
- [ ] T043 [P] Запустить pre-commit hooks: pre-commit run --all-files
- [ ] T044 [P] Запустить mypy проверку: mypy app/
- [ ] T045 [P] Проверить генерацию OpenAPI документации: запустить app, открыть http://localhost:8000/docs
- [ ] T046 [P] Обновить quickstart.md с реальными примерами из реализации
- [ ] T047 Запустить все тесты с покрытием: pytest --cov=app --cov-branch --cov-report=term-missing
- [ ] T048 Создать коммит с изменениями: git add . && git commit -m "Implement authentication and authorization with JWT"

**Критерий завершения**: Все тесты проходят, покрытие > 90%, pre-commit hooks не выдают ошибок, документация актуальна.

**Зависимости**: Требует завершения всех предыдущих фаз (Setup, Foundational, US1, US2, US3).

---

## Dependency Graph (Граф зависимостей)

```
Phase 1 (Setup)
    ├─ T001: python-jose dependency
    ├─ T002: AuthErrorMessage enum
    └─ T003: JWTConfig
         ↓
Phase 2 (Foundational)
    ├─ T004: BlacklistedToken model
    ├─ T005: BlacklistedTokenCrud
    ├─ T006: models/__init__.py
    ├─ T007: Alembic migration
    ├─ T008: Apply migration
    ├─ T009: Auth fixtures
    └─ T010: JWT helper functions
         ↓
    ├──────────────────────────────────────┐
         ↓                                  ↓
Phase 3 (US1: Auth)                  Phase 4 (US2: Logout)
    ├─ T011-T013: Schemas              ├─ T024: AuthService.logout
    ├─ T014-T019: Controllers          ├─ T025-T026: Logout endpoint
    ├─ T020-T021: Tests                ├─ T027-T028: Dependencies
    └─ T022-T023: Integration          ├─ T029-T030: Tests
         ↓                              └─ T031-T032: Integration
         ↓
    ┌────────────────────────────────────────┐
         ↓
Phase 5 (US3: Authorization)
    ├─ T033: get_current_user update
    ├─ T034-T037: Protect endpoints
    ├─ T038-T039: Tests
    └─ T040-T041: Integration
         ↓
Phase 6 (Polish)
    └─ T042-T048: Final checks
```

**Пояснение**:
- Phase 1 и Phase 2 должны быть завершены полностью до начала любой user story
- US1 (Phase 3) независима и может быть реализована первой
- US2 (Phase 4) требует US1 (для тестирования logout нужен рабочий login)
- US3 (Phase 5) требует US1 и US2 (нужен get_current_user из US2)
- Phase 6 (Polish) требует завершения всех user stories

---

## Parallel Execution Examples (Примеры параллельного выполнения)

### В Phase 1 (Setup):
```
T002 (AuthErrorMessage enum) ← можно параллельно с → T003 (JWTConfig)
```

### В Phase 2 (Foundational):
```
T005 (BlacklistedTokenCrud) ← можно параллельно с → T009 (Auth fixtures)
T010 (JWT helpers) ← можно параллельно с → T006 (models/__init__.py)
```

### В Phase 3 (US1 - Аутентификация):
```
T011 (AuthRequest/Response) ← можно параллельно с → T013 (LogoutResponse schema)
T020 (AuthService tests) ← можно параллельно с → T021 (Auth endpoint tests)
```

### В Phase 4 (US2 - Выход из системы):
```
T027 (get_current_user) ← можно параллельно с → T028 (oauth2_scheme)
T029 (Logout service tests) ← можно параллельно с → T030 (Logout endpoint tests)
```

### В Phase 5 (US3 - Авторизация):
```
T034 (Protect GET user) ← можно параллельно с → T035 (Protect PUT user) →
                                                             ←
T036 (Protect DELETE user) ← можно параллельно с → T037 (Protect LIST users)

T038 (get_current_user tests) ← можно параллельно с → T039 (Protected endpoints tests)
```

### В Phase 6 (Polish):
```
T043 (pre-commit) ← можно параллельно с → T044 (mypy) →
                                               ←
T045 (OpenAPI docs) ← можно параллельно с → T046 (Update quickstart.md)
```

---

## Summary (Резюме)

### Распределение задач по фазам

| Фаза | Описание | Кол-во задач | Параллельных |
|------|----------|--------------|--------------|
| Phase 1 | Setup (Настройка) | 3 | 2 |
| Phase 2 | Foundational (Фундамент) | 7 | 2 |
| Phase 3 | US1: Аутентификация | 13 | 2 |
| Phase 4 | US2: Выход из системы | 9 | 2 |
| Phase 5 | US3: Авторизация | 8 | 4 |
| Phase 6 | Polish (Доработка) | 7 | 3 |
| **Итого** | | **47** | **15** |

### Распределение задач по типам

| Тип задач | Количество |
|-----------|------------|
| Модели (Models) | 1 (T004) |
| CRUD | 1 (T005) |
| Сервисы (Services) | 3 (T012, T024, T033) |
| Контроллеры (Controllers) | 8 (T014-T019, T025-T026) |
| Pydantic схемы (Schemas) | 2 (T011, T013) |
| Роутинг | 1 (T019) |
| Dependency Injection | 2 (T027-T028) |
| Тесты | 8 (T020-T021, T029-T030, T038-T039) |
| Миграции БД | 2 (T007-T008) |
| Конфигурация | 1 (T003) |
| Enum'ы | 1 (T002) |
| Фикстуры | 2 (T009-T010) |
| Интеграция | 5 (T022-T023, T031-T032, T040-T041) |
| Полировка | 7 (T042-T048) |
| Зависимости | 1 (T001) |

### Критерии успеха для каждой User Story

#### US1 (Аутентификация) - P1
- ✅ POST /auth/login работает для валидных email/password
- ✅ Возвращает JWT токен с user_id, is_active, exp, iat, jti
- ✅ Возвращает 401 "Неверный email или пароль" для неверных учетных данных
- ✅ Возвращает 401 "Учётная запись неактивна" для is_active=False
- ✅ Все тесты проходят, покрытие > 90%

#### US2 (Выход из системы) - P2
- ✅ POST /auth/logout добавляет токен в blacklist
- ✅ Отозванные токены отклоняются с ошибкой 401
- ✅ Повторный logout с тем же токеном возвращает ошибку
- ✅ Все тесты проходят, покрытие > 90%

#### US3 (Авторизация) - P3
- ✅ Все защищённые эндпоинты требуют валидный токен
- ✅ Публичные эндпоинты (POST /users/, POST /auth/login) доступны без токена
- ✅ Токены с is_active=False отклоняются с ошибкой 401
- ✅ Отозванные токены отклоняются с ошибкой 401
- ✅ Все тесты проходят, покрытие > 90%

---

## Следующие шаги

1. **Начать с Phase 1 (Setup)**: Выполнить задачи T001-T003
2. **Продолжить Phase 2 (Foundational)**: Выполнить задачи T004-T010
3. **Реализовать MVP**: Phase 3 (US1) - задачи T011-T023
4. **Инкрементально добавить**:
   - US2 (Phase 4) - задачи T024-T032
   - US3 (Phase 5) - задачи T033-T041
5. **Финальная полировка**: Phase 6 - задачи T042-T048

После завершения всех задач, функция готова к продакшену!
