# API Contract: Поиск пользователей

**Version**: 1.0
**Base Path**: `/api/v1/users/`
**Date**: 2025-02-06

## Endpoints

### GET /api/v1/users/

Поиск пользователей в системе. Поддерживает два режима:
1. Поиск конкретного пользователя по email (если указан параметр `email`)
2. Получение списка всех пользователей (если параметр `email` не указан)

---

#### Request

**Method**: `GET`

**Path**: `/api/v1/users/`

**Query Parameters**:

| Параметр | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| `email` | string (email) | Нет | `null` | Email пользователя для поиска. Поиск выполняется без учета регистра. |

**Headers**:
```
Content-Type: application/json
```

**Request Body**: Нет

**Примеры запросов**:

```bash
# Поиск пользователя по email
GET /api/v1/users/?email=test@example.com

# Получение всех пользователей
GET /api/v1/users/
```

---

#### Response

**Success Response** (код `200 OK`)

**Сценарий 1**: Пользователь найден по email

**Content-Type**: `application/json`

**Body**:
```json
{
  "id": 1,
  "email": "test@example.com",
  "first_name": "Иван",
  "last_name": "Иванов"
}
```

**Сценарий 2**: Возвращен список всех пользователей

**Content-Type**: `application/json`

**Body**:
```json
[
  {
    "id": 1,
    "email": "user1@example.com",
    "first_name": "Иван",
    "last_name": "Иванов"
  },
  {
    "id": 2,
    "email": "user2@example.com",
    "first_name": "Петр",
    "last_name": "Петров"
  },
  {
    "id": 3,
    "email": "user3@example.com",
    "first_name": "Сидор",
    "last_name": "Сидоров"
  }
]
```

**Сценарий 3**: Пустой список пользователей

**Content-Type**: `application/json`

**Body**: `[]`

---

#### Error Responses

**Ошибка 1**: Пользователь не найден

**Код**: `404 Not Found`

**Content-Type**: `application/json`

**Body**:
```json
{
  "detail": "Пользователь с указанным email не найден"
}
```

**Пример**: Запрос `GET /api/v1/users/?email=notfound@example.com` когда пользователь не существует

---

**Ошибка 2**: Невалидный формат email

**Код**: `422 Unprocessable Entity`

**Content-Type**: `application/json`

**Body**:
```json
{
  "detail": [
    {
      "type": "email_type",
      "msg": "value is not a valid email address",
      "loc": ["query", "email"],
      "input": "invalid-email"
    }
  ]
}
```

**Пример**: Запрос `GET /api/v1/users/?email=invalid-email` (без @, домена и т.д.)

---

#### Сценарии использования

**1. Администратор ищет конкретного пользователя**

**Request**:
```http
GET /api/v1/users/?email=admin@example.com HTTP/1.1
Host: api.example.com
```

**Response** (200 OK):
```json
{
  "id": 1,
  "email": "admin@example.com",
  "first_name": "Админ",
  "last_name": "Администратор"
}
```

---

**2. Администратор получает список всех пользователей**

**Request**:
```http
GET /api/v1/users/ HTTP/1.1
Host: api.example.com
```

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "email": "admin@example.com",
    "first_name": "Админ",
    "last_name": "Администратор"
  },
  {
    "id": 2,
    "email": "user@example.com",
    "first_name": "Иван",
    "last_name": "Иванов"
  }
]
```

---

**3. Администратор ищет пользователя по email (без учета регистра)**

**Request**:
```http
GET /api/v1/users/?email=Test@Example.COM HTTP/1.1
Host: api.example.com
```

**Response** (200 OK):
```json
{
  "id": 1,
  "email": "test@example.com",
  "first_name": "Тест",
  "last_name": "Тестов"
}
```

---

**4. Администратор ищет несуществующего пользователя**

**Request**:
```http
GET /api/v1/users/?email=notfound@example.com HTTP/1.1
Host: api.example.com
```

**Response** (404 Not Found):
```json
{
  "detail": "Пользователь с указанным email не найден"
}
```

---

**5. Администратор передает невалидный email**

**Request**:
```http
GET /api/v1/users/?email=not-an-email HTTP/1.1
Host: api.example.com
```

**Response** (422 Unprocessable Entity):
```json
{
  "detail": [
    {
      "type": "email_type",
      "msg": "value is not a valid email address",
      "loc": ["query", "email"],
      "input": "not-an-email"
    }
  ]
}
```

---

## Контрактные обязательства

### Обязательства API

✅ **Поведение**:
- Возвращает `200 OK` для успешного поиска
- Возвращает `404 Not Found` если пользователь с указанным email не найден
- Возвращает `422 Unprocessable Entity` при невалидном формате email
- Поиск по email выполняется без учета регистра
- Никогда не возвращает поле `password_hash` в ответе

✅ **Производительность**:
- Поиск по email: < 1 секунда
- Получение списка до 10,000 пользователей: < 2 секунды

✅ **Формат данных**:
- Все ответы в формате JSON
- Даты в ISO 8601 формате (если присутствуют)
- Кодировка UTF-8

✅ **Локализация**:
- Сообщения об ошибках на русском языке

### Обязательства клиента

✅ **Валидация**:
- Клиент должен передавать валидный email в параметре `email`
- Клиент должен обрабатывать все статус коды (200, 404, 422)

✅ **Обработка пустого списка**:
- Клиент должен корректно обрабатывать пустой массив `[]` когда пользователей нет

## OpenAPI Specification

Автоматически генерируется FastAPI. Доступна на `/docs` или `/openapi.json` при запущенном сервере.

**Краткое описание endpoint**:
```yaml
/users/:
  get:
    summary: Поиск пользователей
    description: Поиск пользователя по email или получение списка всех пользователей
    parameters:
      - name: email
        in: query
        required: false
        schema:
          type: string
          format: email
    responses:
      '200':
        description: Успешный поиск
        content:
          application/json:
            schema:
              oneOf:
                - $ref: '#/components/schemas/UserSearchResponse'
                - type: array
                  items:
                    $ref: '#/components/schemas/UserSearchResponse'
      '404':
        description: Пользователь не найден
      '422':
        description: Невалидный формат email
```

## Схемы данных (Schemas)

### UserSearchResponse

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "integer",
      "description": "Уникальный идентификатор пользователя"
    },
    "email": {
      "type": "string",
      "format": "email",
      "description": "Email адрес пользователя"
    },
    "first_name": {
      "type": "string",
      "description": "Имя пользователя"
    },
    "last_name": {
      "type": "string",
      "description": "Фамилия пользователя"
    }
  },
  "required": ["id", "email", "first_name", "last_name"]
}
```

## Версионирование

**Текущая версия**: v1

**Совместимость**:
- Breaking changes потребуют увеличения версии до v2
- Добавление новых query parameters не является breaking change