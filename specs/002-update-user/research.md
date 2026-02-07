# Research: Update User via API

**Feature**: 002-update-user
**Date**: 2025-02-05
**Status**: Complete

## Overview

Данный документ содержит результаты исследования технических решений для реализации API-эндпоинта обновления пользователя. Исследование основано на анализе существующей кодовой базы фичи "001-create-user" и определении паттернов для повторного использования.

## Решения по архитектуре

### Decision 1: Использовать существующую архитектуру CRUD → Service → Controller

**Rationale**:
- Существующий код фичи "001-create-user" уже реализует чистую архитектуру с разделением слоёв
- BaseCrud предоставляет метод `update_one_or_none()` который идеально подходит для обновления
- UserService уже содержит бизнес-логику для валидации email uniqueness и хеширования паролей
- Конституция (принцип V) mandates использование этой архитектуры

**Alternatives considered**:
- Выполнить логику напрямую в контроллере: отклонено, т.к. нарушает принцип V конституции (чистая архитектура)
- Создать отдельный UpdateService: отклонено, т.к. избыточно для простого update

**Implementation**:
- Добавить метод `update_user()` в UserService
- Использовать BaseCrud.update_one_or_none() для операции обновления
- Добавить PUT endpoint в users controller

### Decision 2: Pydantic схемы с переиспользуемыми валидаторами

**Rationale**:
- Существующие валидаторы в UserCreateRequest могут быть переиспользованы
- Pydantic V2 позволяет вынести валидацию в отдельные методы для переиспользования
- Избежим дублирования кода валидации

**Alternatives considered**:
- Скопировать валидацию в новые схемы: отклонено, т.к. нарушает DRY принцип
- Создать базовый класс с валидаторами: отклонено, т.к. over-engineering для 2-х схем

**Implementation**:
- Создать UserUpdateRequest и UserUpdateResponse схемы
- Вынести общие валидаторы имен и пароля в отдельные функции или reusable mixin
- Использовать EmailStr из pydantic для валидации email

### Decision 3: Хеширование паролей через существующий hash_password()

**Rationale**:
- Функция hash_password() уже использует bcrypt 4.0.1 через passlib
- Соответствует принципу I конституции (bcrypt 4.0.1 фиксирован)
- Не нужно дублировать логику хеширования

**Alternatives considered**:
- Использовать другой алгоритм: отклонено, т.к. противоречит конституции
- Хешировать в контроллере: отклонено, т.к. бизнес-логика должна быть в Service слое

**Implementation**:
- Переиспользовать существующую функцию hash_password() из user_service.py
- Вызывать хеширование в UserService.update_user() перед обновлением в БД

### Decision 4: Проверка email uniqueness при update

**Rationale**:
- Email должен быть уникальным во всей системе (FR-004)
- При обновлении email нужно проверить, что новый email не занят другим пользователем
- Существующий метод UsersCrud.email_exists() может быть переиспользован

**Alternatives considered**:
- Полагаться только на constraint БД: отклонено, т.к. даёт неинформативную ошибку 500 вместо 400
- Не проверять при update: отклонено, т.к. нарушает FR-004

**Implementation**:
- Добавить проверку email uniqueness в UserService.update_user()
- Исключить текущего пользователя из проверки (если email не меняется)
- Возвращать HTTP 400 если email уже занят

### Decision 5: Обработка частичных обновлений (optional fields)

**Rationale**:
- FR-013 требует поддержки частичных обновлений
- Pydantic V2 поддерживает optional fields через Optional[T] | None
- Не все поля могут быть предоставлены в запросе

**Alternatives considered**:
- Требовать все поля обязательно: отклонено, т.к. противоречит FR-013
- Использовать PATCH вместо PUT: отклонено, т.к. spec.md явно указывает PUT

**Implementation**:
- Использовать Optional[str] | None для всех полей в UserUpdateRequest
- В UserService обновлять только те поля, которые не None
- Проверять валидацию только для предоставленных полей

## Технологические детали

### Валидация имен (first_name, last_name)

**Существующая реализация** (app/api/v1/schemas/users.py:30-36):
```python
if not re.match(r'^[А-Яа-яA-Za-z\-]+$', v):
    raise ValueError('Должно содержать только русские/английские буквы и тире')
if len(v) > 100:
    raise ValueError('Длина не должна превышать 100 символов')
```

**Переиспользование**: Вынести в отдельную функцию для использования в UserUpdateRequest

### Валидация пароля

**Существующая реализация** (app/api/v1/schemas/users.py:52-83):
- Длина: 8-100 символов
- Минимум 1 заглавная буква [A-Z]
- Минимум 1 строчная буква [a-z]
- Минимум 1 цифра \d

**Переиспользование**: Вынести в отдельную функцию для использования в UserUpdateRequest

### HTTP статусы

**Из spec.md**:
- 200: Успешное обновление
- 404: Пользователь не найден
- 400: Email уже существует
- 422: Ошибка валидации

**Существующие паттерны**:
- HTTP_409_CONFLICT используется для duplicate email в create
- Для update будем использовать HTTP_400_BAD_REQUEST (как указано в spec.md)

### BaseCrud.update_one_or_none()

**Сигнатура** (app/db/crud/base.py:80-95):
```python
async def update_one_or_none(
    self, session: AsyncSession, filter_by: Mapping[str, Any], values: Mapping[str, Any]
) -> ModelType | None
```

**Особенности**:
- Возвращает None если запись не найдена
- Использует SQLAlchemy 2.0 update() с returning()
- Автоматически коммитит изменения

## Неопределённости, требующие уточнения

Отсутствуют. Все технические решения определены на основе анализа существующей кодовой базы и конституции.

## Зависимости от других компонентов

### Существующие зависимости (переиспользование):
- app/db/models/user.py: User модель (не требует изменений)
- app/db/crud/base.py: BaseCrud.update_one_or_none() (готов к использованию)
- app/db/crud/users.py: UsersCrud.email_exists() (готов к использованию)
- app/services/user_service.py: hash_password() (готов к использованию)

### Новые зависимости:
- app/api/v1/schemas/users.py: UserUpdateRequest, UserUpdateResponse (новые схемы)
- app/api/v1/controllers/users.py: PUT /{user_id} endpoint (новый handler)
- app/services/user_service.py: update_user() method (новый метод)

## Best Practices изученных технологий

### FastAPI PUT endpoints
- Использовать path parameter для user_id: `/{user_id}`
- Использовать response_model для документации ответа
- Валидация request body через Pydantic автоматически

### Pydantic V2 validators
- @field_validator для валидации отдельных полей
- @model_validator для валидации нескольких полей вместе
- Могут быть переиспользованы через наследование или вынесение в функции

### SQLAlchemy 2.0 async update
- Использовать update().where().values().returning()
- synchronize_session='fetch' для получения обновлённой записи
- Автоматический commit через session.commit()

## Производительность и масштабирование

### Производительность:
- Цель: < 2 секунд на обновление (SC-001)
- Цель: < 500мс на валидацию и ошибки (SC-002)
- BaseCrud.update_one_or_none() выполняет один SQL запрос
- Email uniqueness проверяется отдельным запросом (можно оптимизировать в будущем)

### Масштабирование:
- Single database instance с PostgreSQL 17
- Connection pooling через AsyncPG
- Нет требований к горизонтальному масштабированию

## Безопасность

### Хеширование паролей:
- bcrypt 4.0.1 с passlib (фиксированная версия из конституции)
- Соль добавляется автоматически через bcrypt
- rounds=12 (по умолчанию в passlib)

### Валидация входных данных:
- Email: Pydantic EmailStr (валидация формата)
- Имена: Regex валидация (только буквы и дефисы)
- Пароль: Complexity checks (длина, регистр, цифры)

### Защита от race conditions:
- IntegrityError handling при дубликатах email (из create_user)
- Может быть переиспользован для update

## Тестирование

### Существующие фикстуры (tests/conftest.py):
- db_session: асинхронная сессия с rollback
- async_client: HTTP клиент с подменой БД
- faker: генератор тестовых данных
- valid_user_request: Pydantic схема с валидными данными

### Новые фикстуры для update:
- update_user_request: Pydantic схема для update запроса
- existing_user: фикстура для создания пользователя перед update

### Покрытие тестами:
- Успешное обновление всех полей
- Частичное обновление (отдельные поля)
- Попытка duplicate email
- Обновление несуществующего user_id (404)
- Невалидные данные (422)
- Edge cases (пустые поля, экстремально длинные значения)

## Следующие шаги (Phase 1)

1. **data-model.md**: Описать сущности User, UpdateRequest, UpdateResponse
2. **contracts/**: Создать OpenAPI спецификацию для PUT /users/{id}
3. **Update agent context**: Добавить новые схемы и endpoint в контекст Claude