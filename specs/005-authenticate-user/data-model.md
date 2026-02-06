# Модель данных: Аутентификация и авторизация

**Дата**: 2025-02-06
**Фича**: 005-authenticate-user

## Обзор

Документ описывает модель данных для функции аутентификации и авторизации пользователей. Функция добавляет одну новую таблицу для отслеживания отозванных токенов и использует существующую модель User.

## Новые сущности

### BlacklistedToken

**Назначение**: Хранение отозванных JWT токенов для реализации функции выхода из системы (logout).

**Описание**: Когда пользователь выходит из системы, его токен добавляется в чёрный список. При последующих запросах проверяется, нет ли токена в чёрном списке.

**Поля**:

| Поле | Тип | Обязательное | Описание | Валидация |
|------|-----|--------------|----------|-----------|
| id | Integer | Да | Первичный ключ | Auto-increment |
| token_jti | String(255) | Да | Уникальный идентификатор токена (JWT ID) | Unique, Not null |
| user_id | Integer | Да | ID пользователя, которому был выдан токен | Foreign key → users.id, Not null |
| revoked_at | DateTime | Да | Время отзыва токена | Not null, default=now() |
| expires_at | DateTime | Да | Время истечения токена (из JWT exp claim) | Not null, используется для очистки |

**Индексы**:
- `UNIQUE` на `token_jti` (быстрая проверка отзыва)
- `INDEX` на `expires_at` (для очистки истёкших токенов)

**Связи**:
- **ManyToOne**: BlacklistedToken → User (user_id)
  - Один пользователь может иметь несколько отозванных токенов
  - Используется для аудита и очистки

**State transitions**:
```
[Active Token] --(logout)--> [Blacklisted Token]
                                         |
                                         v (через cron или по запросу)
                                   [Deleted (cleanup)]
```

**Ограничения**:
- Токен с истёкшим `expires_at` может быть удалён из БД (автоочистка)
- Один и тот же `token_jti` не может быть добавлен дважды (уникальность)

## Используемые существующие сущности

### User (уже существует)

**Назначение**: Учётная запись пользователя в системе.

**Используемые поля**:

| Поле | Тип | Использование в auth |
|------|-----|---------------------|
| id | Integer | Идентификатор пользователя в JWT (sub claim) |
| email | String | Уникальный идентификатор для поиска пользователя |
| password_hash | String | Проверка пароля при аутентификации |
| is_active | Boolean | Проверка активного статуса при аутентификации |

**Взаимодействие с auth**:
1. **Аутентификация**: Поиск пользователя по `email`, проверка `password_hash`, проверка `is_active`
2. **Генерация токена**: `user_id` и `is_active` включаются в JWT payload
3. **Авторизация**: `is_active` проверяется при каждом запросе (из токена)

## JWT Payload (JSON Web Token)

**Структура токена**:

```json
{
  "sub": "123",              // Subject: user_id (стандартный claim)
  "user_id": 123,            // Дублирование sub для удобства
  "is_active": true,         // Статус на момент выдачи
  "iat": 1736123456,         // Issued At: время выдачи (Unix timestamp)
  "exp": 1736209856,         // Expiration: время истечения (Unix timestamp)
  "jti": "unique-token-id"   // JWT ID: уникальный идентификатор токена
}
```

**Описание полей**:

| Claim | Тип | Обязательное | Описание |
|-------|-----|--------------|----------|
| sub | String | Да | Subject: ID пользователя (стандарт RFC 7519) |
| user_id | Integer | Да | Дублирование sub для удобства в коде |
| is_active | Boolean | Да | Статус пользователя на момент выдачи токена |
| iat | Integer | Да | Issued At: время выдачи в секундах (Unix timestamp) |
| exp | Integer | Да | Expiration: время истечения в секундах (Unix timestamp) |
| jti | String | Да | JWT ID: уникальный идентификатор для отзыва (UUID) |

**Алгоритм подписи**: HS256 (HMAC-SHA256)

## Pydantic схемы

### AuthRequest (запрос на аутентификацию)

```python
class AuthRequest(BaseModel):
    """Схема запроса на аутентификацию."""

    email: EmailStr
    password: str  # Минимум 8 символов (из требований регистрации)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "Password123"
                }
            ]
        }
    )
```

### AuthResponse (ответ с токеном)

```python
class AuthResponse(BaseModel):
    """Схема ответа с JWT токеном."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Секунды до истечения

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 3600
                }
            ]
        }
    )
```

### LogoutResponse (ответ на выход)

```python
class LogoutResponse(BaseModel):
    """Схема ответа на выход из системы."""

    message: str = "Успешный выход из системы"
```

### ErrorResponse (ошибка аутентификации)

```python
class AuthErrorResponse(BaseModel):
    """Схема ошибки аутентификации."""

    detail: str  # Локализованное сообщение об ошибке

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "detail": "Неверный email или пароль"
                },
                {
                    "detail": "Учётная запись неактивна"
                }
            ]
        }
    )
```

## Конфигурация

### JWT настройки (Pydantic Settings)

```python
class JWTConfig(BaseSettings):
    """Конфигурация JWT."""

    secret_key: str = Field(
        ...,
        description="Секретный ключ для подписи JWT токенов",
        min_length=32
    )
    access_token_expire_minutes: int = Field(
        default=60,
        description="Время жизни токена в минутах",
        ge=1,  # Минимум 1 минута
        le=43200  # Максимум 30 дней
    )
    algorithm: str = Field(
        default="HS256",
        description="Алгоритм подписи JWT"
    )

    class Config:
        env_prefix = "JWT__"  # JWT__SECRET_KEY, JWT__ACCESS_TOKEN_EXPIRE_MINUTES
```

## Диаграмма связей

```
┌─────────────┐         ┌──────────────────┐         ┌──────────────┐
│    User     │         │ BlacklistedToken │         │     JWT      │
│ (существ.)  │         │    (новая)       │         │  (токен)     │
├─────────────┤         ├──────────────────┤         ├──────────────┤
│ id          │<───────│ user_id          │         │ sub (user_id)│
│ email       │         │ token_jti        │<────────│ jti          │
│ password    │         │ revoked_at       │         │ exp          │
│ is_active   │         │ expires_at       │         │ iat          │
└─────────────┘         └──────────────────┘         │ is_active    │
                                                        └──────────────┘
```

**Пояснение**:
1. User → JWT: Генерация токена при аутентификации
2. JWT → BlacklistedToken: Отзыв токена при logout (jti → token_jti)
3. BlacklistedToken → User: Аудит и очистка по user_id

## Миграции БД

### 005_add_blacklisted_tokens.py

**Создание таблицы**:

```sql
CREATE TABLE blacklisted_tokens (
    id SERIAL PRIMARY KEY,
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    revoked_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_blacklisted_tokens_expires_at ON blacklisted_tokens(expires_at);
```

**Очистка истёкших токенов** (опционально):

```sql
DELETE FROM blacklisted_tokens
WHERE expires_at < NOW();
```

## Примечания к производительности

1. **Чтение**: Проверка token_jti в blacklist по UNIQUE индексу (O(log n))
2. **Запись**: Добавление в blacklist только при logout (не при каждом запросе)
3. **Очистка**: Рекомендуется периодически удалять истёкшие токены (cron раз в день)
4. **Каскадное удаление**: Если пользователь удалён, его токены тоже удаляются (ON DELETE CASCADE)

## Безопасность

1. **JWT secret**: Минимум 32 символа, хранится в переменной окружения
2. **Token lifetime**: Параметризуем (от 1 минуты до 30 дней)
3. **Blacklist**: Токен проверяется на каждом защищённом запросе
4. **Password**: НЕ хранится в токене, только проверяется при аутентификации
5. **Email**: НЕ включён в токен (privacy), только user_id