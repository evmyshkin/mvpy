# Data Model: Update User via API

**Feature**: 002-update-user
**Date**: 2025-02-05
**Status**: Final

## Overview

Документ описывает модели данных для фичи обновления пользователя через API. Фича использует существующую модель User и вводит новые Pydantic схемы для валидации запросов и ответов.

## Сущности

### 1. User (SQLAlchemy Model)

**Источник**: `app/db/models/user.py` (существующая модель)

**Описание**: Представляет сотрудника в системе

**Поля**:

| Имя поля | Тип | Описание | Constraints |
|----------|-----|----------|-------------|
| id | int | Уникальный идентификатор | Primary key, auto-increment |
| email | str | Email адрес | Unique, not null, max 255 chars |
| first_name | str | Имя пользователя | Not null, max 100 chars |
| last_name | str | Фамилия пользователя | Not null, max 100 chars |
| password_hash | str | Захешированный пароль | Not null (bcrypt) |
| created_at | datetime | Время создания | Auto-generated, timezone-aware |
| updated_at | datetime | Время обновления | Auto-generated on update, timezone-aware |

**Валидация на уровне БД**:
- `email`: UNIQUE constraint в БД
- `email`, `first_name`, `last_name`, `password_hash`: NOT NULL constraints
- `first_name`, `last_name`: max 100 символов (VARCHAR(100))
- `email`: max 255 символов (VARCHAR(255))

**Отношения**: Нет (на данный момент)

**Изменения**: Не требует изменений для данной фичи

---

### 2. UserUpdateRequest (Pydantic Schema)

**Источник**: `app/api/v1/schemas/users.py` (новая схема)

**Описание**: Схема валидации запроса на обновление пользователя

**Поля**:

| Имя поля | Тип | Обязательное | Валидация |
|----------|-----|--------------|-----------|
| email | EmailStr | Нет | Email формат, max 255 chars, уникальность в БД |
| first_name | str \| None | Нет | Русские/английские буквы и дефисы, max 100 chars |
| last_name | str \| None | Нет | Русские/английские буквы и дефисы, max 100 chars |
| password | str \| None | Нет | Минимум 8 символов, 1 заглавная, 1 строчная, 1 цифра, max 100 chars |

**Правила валидации**:

1. **Email** (если предоставлен):
   - Валидный email формат (через Pydantic EmailStr)
   - Максимум 255 символов
   - Не должен совпадать с email другого пользователя

2. **first_name, last_name** (если предоставлены):
   - Regex: `^[А-Яа-яA-Za-z\-]+$` (только буквы кириллицы/латиницы и дефис)
   - Длина: 1-100 символов
   - Не может быть пустой строкой

3. **password** (если предоставлен):
   - Длина: 8-100 символов
   - Минимум 1 заглавная буква [A-Z]
   - Минимум 1 строчная буква [a-z]
   - Минимум 1 цифра [0-9]

**Пример валидного запроса**:
```json
{
  "email": "newemail@example.com",
  "first_name": "Иван",
  "last_name": "Иванов",
  "password": "NewSecure123"
}
```

**Пример частичного обновления**:
```json
{
  "first_name": "Петр"
}
```

**Пример невалидного запроса**:
```json
{
  "email": "invalid-email",
  "first_name": "John123",
  "password": "simple"
}
```

---

### 3. UserUpdateResponse (Pydantic Schema)

**Источник**: `app/api/v1/schemas/users.py` (новая схема)

**Описание**: Схема ответа при успешном обновлении пользователя

**Поля**:

| Имя поля | Тип | Описание |
|----------|-----|----------|
| id | int | Уникальный идентификатор пользователя |
| email | str | Email адрес пользователя |
| first_name | str | Имя пользователя |
| last_name | str | Фамилия пользователя |

**Примечание**: Пароль не возвращается в ответе (только password_hash хранится в БД)

**Пример ответа**:
```json
{
  "id": 1,
  "email": "newemail@example.com",
  "first_name": "Иван",
  "last_name": "Иванов"
}
```

---

## State Transitions

User не имеет явных состояний (state machine). Обновление полей не меняет состояние пользователя, а только модифицирует атрибуты.

**Возможные переходы при update**:

| Сценарий | Изменения полей | HTTP статус |
|----------|----------------|-------------|
| Успешное обновление | Любые комбинации полей | 200 OK |
| User не найден | - | 404 Not Found |
| Duplicate email | email → существующий email | 400 Bad Request |
| Валидация не пройдена | Невалидные данные | 422 Unprocessable Entity |

---

## Relationships

### User relationships (текущие и будущие)

**Текущие**: Нет отношений

**Потенциальные будущие отношения** (не в scope данной фичи):
- User ← Order (один пользователь может иметь много заказов)
- User ← Session (один пользователь может иметь много сессий)
- User ← Role (многие-ко-многим для RBAC)

---

## Data Flow

### Flow 1: Успешное обновление всех полей

```
1. Client отправляет PUT /api/v1/users/1 с JSON body
   ↓
2. FastAPI валидирует request body через UserUpdateRequest
   - Pydantic проверяет email формат
   - Pydantic проверяет имя regex
   - Pydantic проверяет пароль complexity
   ↓
3. Controller получает user_id из path parameter
   ↓
4. UserService.update_user() выполняет:
   a. Проверяет существование user (через BaseCrud)
   b. Проверяет email uniqueness (если email изменился)
   c. Хеширует пароль (если password предоставлен)
   d. Обновляет запись через BaseCrud.update_one_or_none()
   ↓
5. БД обновляет запись и возвращает обновлённый объект
   ↓
6. UserService маппит User → UserUpdateResponse
   ↓
7. Controller возвращает response с HTTP 200
```

### Flow 2: Duplicate email

```
1. Client отправляет PUT /api/v1/users/1 с email="existing@example.com"
   ↓
2. Pydantic валидация проходит (email format валиден)
   ↓
3. UserService.update_user() проверяет email uniqueness
   ↓
4. UsersCrud.email_exists() возвращает True
   ↓
5. UserService raise HTTPException(status_code=400)
   ↓
6. Controller возвращает HTTP 400 с ошибкой
```

### Flow 3: User not found

```
1. Client отправляет PUT /api/v1/users/999
   ↓
2. Pydantic валидация проходит
   ↓
3. UserService.update_user() вызывает BaseCrud.update_one_or_none()
   ↓
4. BaseCrud возвращает None (запись не найдена)
   ↓
5. UserService raise HTTPException(status_code=404)
   ↓
6. Controller возвращает HTTP 404 с ошибкой
```

---

## Validation Strategy

### Валидация на разных уровнях

1. **Pydantic (Schema level)**:
   - Email формат (EmailStr)
   - Regex для имен
   - Complexity для пароля
   - Длина полей
   - Автоматически возвращает 422 при ошибках

2. **Service (Business logic level)**:
   - Email uniqueness (проверка в БД)
   - User existence
   - Хеширование пароля

3. **Database (Constraint level)**:
   - Unique constraint на email (защита от race conditions)
   - Not null constraints
   - Max length constraints

---

## Migration Requirements

**Изменения схемы БД**: Не требуются

Существующая модель User уже содержит все необходимые поля:
- `email`, `first_name`, `last_name`, `password_hash`
- Уникальный constraint на email
- Timestamps (created_at, updated_at)

**Обновление Alembic миграций**: Не требуется

---

## Indexes

**Существующие индексы** (из User модели):
- Primary key: `id`
- Unique index: `email` (через unique=True в модели)

**Новые индексы**: Не требуются

---

## Security Considerations

### Пароли
- Plaintext пароли никогда не хранятся в БД
- Хеширование через bcrypt 4.0.1 перед сохранением
- Пароли не возвращаются в API ответах

### Email uniqueness
- Проверка на уровне Service для информативных ошибок
- Unique constraint в БД для защиты от race conditions

### Валидация входных данных
- Regex для имен предотвращает injection специальных символов
- Сложность пароля предотвращает слабые пароли
- Email формат предотвращает malformed данные

---

## Performance Considerations

### SQL запросы при update:

1. **Проверка email uniqueness** (если email изменился):
   ```sql
   SELECT * FROM users WHERE email = ? AND id != ?
   ```

2. **Update пользователя**:
   ```sql
   UPDATE users
   SET email = ?, first_name = ?, last_name = ?, password_hash = ?
   WHERE id = ?
   RETURNING *
   ```

**Итого**: 1-2 SQL запроса на один update

### Оптимизации (текущие и будущие):

**Текущие**:
- BaseCrud.update_one_or_none() использует returning() для получения обновлённой записи за один запрос

**Потенциальные будущие** (не в scope):
- Batch updates для множественных обновлений
- Caching для email uniqueness проверок

---

## Testing Data Model

### Unit тесты для Pydantic схем:

```python
# Валидные данные
test_valid_update_request()

# Частичное обновление
test_partial_update_request()

# Невалидный email
test_invalid_email_format()

# Невалидные имена (цифры, символы)
test_invalid_name_characters()

# Слабый пароль
test_weak_password()

# Превышение длины полей
test_field_too_long()
```

### Integration тесты:

```python
# Успешное обновление
test_update_user_success()

# Duplicate email
test_update_user_duplicate_email()

# User not found
test_update_user_not_found()

# Валидация ошибок
test_update_user_validation_errors()

# Частичное обновление
test_update_user_partial_fields()
```

---

## Glossary

- **bcrypt**: Криптографическая функция хеширования для безопасного хранения паролей
- **EmailStr**: Pydantic тип для валидации email формата
- **field_validator**: Декоратор Pydantic V2 для валидации отдельных полей
- **Unique constraint**: Ограничение уникальности на уровне БД
- **Race condition**: Состояние гонки при конкурентных запросах
- **Returning clause**: SQLAlchemy конструкция для возврата обновлённых записей