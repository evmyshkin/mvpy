# API Contract: Поиск пользователей

**Version**: 1.0
**Base Path**: `/api/v1/users/`
**Date**: 2025-02-06

## Endpoints

### GET /api/v1/users/{user_id}

Получение информации о конкретном пользователе по ID.

---

#### Request

**Method**: `GET`

**Path**: `/api/v1/users/{user_id}`

**Path Parameters**:

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `user_id` | integer | Да | Уникальный идентификатор пользователя |

**Headers**:
```
Content-Type: application/json
```

**Request Body**: Нет

**Примеры запросов**:

```bash
# Получение пользователя по ID
GET /api/v1/users/1

# Получение пользователя с ID=42
GET /api/v1/users/42
```

---

#### Response

**Success Response** (код `200 OK`)

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

---

#### Error Responses

**Ошибка 1**: Пользователь не найден

**Код**: `404 Not Found`

**Content-Type**: `application/json`

**Body**:
```json
{
  "detail": "Пользователь не найден"
}
```

**Пример**: Запрос `GET /api/v1/users/99999` когда пользователь не существует

---

**Ошибка 2**: Невалидный формат ID

**Код**: `422 Unprocessable Entity`

**Content-Type**: `application/json`

**Body**:
```json
{
  "detail": [
    {
      "type": "int_parsing",
      "msg": "Input should be a valid integer",
      "loc": ["path", "user_id"],
      "input": "abc"
    }
  ]
}
```

**Пример**: Запрос `GET /api/v1/users/abc` (строка вместо числа)

---

#### Сценарии использования

**1. Администратор получает пользователя по ID**

**Request**:
```http
GET /api/v1/users/1 HTTP/1.1
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

**2. Администратор ищет несуществующего пользователя**

**Request**:
```http
GET /api/v1/users/99999 HTTP/1.1
Host: api.example.com
```

**Response** (404 Not Found):
```json
{
  "detail": "Пользователь не найден"
}
```

---

**3. Администратор передает невалидный ID**

**Request**:
```http
GET /api/v1/users/abc HTTP/1.1
Host: api.example.com
```

**Response** (422 Unprocessable Entity):
```json
{
  "detail": [
    {
      "type": "int_parsing",
      "msg": "Input should be a valid integer",
      "loc": ["path", "user_id"],
      "input": "abc"
    }
  ]
}
```

---

## GET /api/v1/users/

Получение списка всех пользователей.

---

#### Request

**Method**: `GET`

**Path**: `/api/v1/users/`

**Headers**:
```
Content-Type: application/json
```

**Request Body**: Нет

**Примеры запросов**:

```bash
# Получение всех пользователей
GET /api/v1/users/
```

---

#### Response

**Success Response** (код `200 OK`)

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
  }
]
```

**Пустой список**:
```json
[]
```

---

## Контрактные обязательства

### Обязательства API

✅ **Поведение**:
- Возвращает `200 OK` для успешного поиска пользователя по ID
- Возвращает `200 OK` для списка всех пользователей (включая пустой список)
- Возвращает `404 Not Found` если пользователь с указанным ID не найден
- Возвращает `422 Unprocessable Entity` при невалидном формате ID
- Никогда не возвращает поле `password_hash` в ответе

✅ **Производительность**:
- Поиск по ID: < 1 секунды
- Получение списка до 10,000 пользователей: < 2 секунды

✅ **Формат данных**:
- Все ответы в формате JSON
- Даты в ISO 8601 формате (если присутствуют)
- Кодировка UTF-8

✅ **Локализация**:
- Сообщения об ошибках на русском языке

### Обязательства клиента

✅ **Валидация**:
- Клиент должен передавать валидный integer ID в path параметре
- Клиент должен обрабатывать все статус коды (200, 404, 422)

✅ **Обработка пустого списка**:
- Клиент должен корректно обрабатывать пустой массив `[]` когда пользователей нет

## OpenAPI Specification

Автоматически генерируется FastAPI. Доступна на `/docs` или `/openapi.json` при запущенном сервере.

**Краткое описание endpoints**:
```yaml
/users/{user_id}:
  get:
    summary: Получить пользователя по ID
    description: Получение информации о конкретном пользователе
    parameters:
      - name: user_id
        in: path
        required: true
        schema:
          type: integer
    responses:
      '200':
        description: Пользователь найден
      '404':
        description: Пользователь не найден
      '422':
        description: Невалидный формат ID

/users/:
  get:
    summary: Получить список всех пользователей
    description: Получение списка всех зарегистрированных пользователей
    responses:
      '200':
        description: Список пользователей (может быть пустым)
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