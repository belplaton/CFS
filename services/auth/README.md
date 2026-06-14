# Auth Service

Сервис аутентификации и управления пользователями для Cloud File Storage (CFS).

## Стек

| Компонент | Технология |
|---|---|
| Framework | FastAPI (async) |
| ASGI-сервер | Uvicorn |
| База данных | PostgreSQL 15 (SQLAlchemy 2.0 async + asyncpg) |
| Миграции | Alembic |
| Аутентификация | JWT (python-jose) — access + refresh токены с claims `iss`/`aud` |
| Пароли | bcrypt (passlib) |
| Кэш / Rate-limiting | Redis (redis-py async) |
| Логирование | structlog (JSON в production, цветной консоль в dev) |
| Тестирование | pytest + pytest-asyncio + testcontainers (Postgres) |

## Структура проекта

```
src/
├── main.py                  # FastAPI app, lifespan, middleware
├── config.py                # Pydantic Settings (из env)
├── exceptions.py            # Иерархия доменных ошибок
├── api/
│   ├── __init__.py          # Агрегация роутеров
│   ├── auth.py              # /api/auth/* эндпоинты
│   ├── users.py             # /api/users/* внутренние эндпоинты
│   ├── health.py            # /health проверка
│   └── exception_handlers.py
├── models/
│   ├── __init__.py          # Engine, session factory, get_db
│   ├── user.py              # User ORM модель (UUID PK)
│   └── token.py             # VerificationToken модель
├── schemas/                 # Pydantic модели запросов/ответов
├── services/
│   └── user_service.py      # Бизнес-логика
├── repositories/
│   ├── user.py              # SQL-запросы для User
│   └── verification_token.py
├── middleware/
│   ├── request_id.py        # Проброс X-Request-ID
│   └── access_log.py        # Структурированное логирование доступа
└── utils/
    ├── security.py          # JWT + bcrypt утилиты
    ├── dependencies.py      # get_current_user, get_current_verified_user
    ├── rate_limiter.py      # Rate limiting на Redis
    ├── redis_client.py      # Async Redis синглтон (no-op заглушка)
    └── logging.py           # Конфигурация structlog
```

## Быстрый старт

### Docker Compose (рекомендуется)

```bash
docker compose up --build
```

Сервис будет доступен на внутреннем порту `8000` (проксируется через gateway на `http://localhost:8080/api/auth`).

### Локальная разработка

```bash
cp .env.example .env   # заполнить секреты
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Переменные окружения

| Переменная | Обязательна | По умолчанию | Описание |
|---|---|---|---|
| `ENV` | Нет | `development` | `development` / `production` |
| `DATABASE_URL` | Нет | `postgresql+asyncpg://...` | Async строка подключения к PostgreSQL |
| `JWT_SECRET` | **Да** | — | HMAC-секрет для подписи JWT |
| `JWT_ALGORITHM` | Нет | `HS256` | Алгоритм подписи JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Нет | `30` | Время жизни access токена |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Нет | `7` | Время жизни refresh токена |
| `JWT_ISSUER` | Нет | `auth-service` | Claim `iss` — должен совпадать с downstream-сервисами |
| `JWT_AUDIENCE` | Нет | `cloud-storage` | Claim `aud` — должен совпадать с downstream-сервисами |
| `SERVICE_API_KEY` | **Да** | — | Общий секрет для межсервисных вызовов (`X-API-Key`) |
| `REDIS_URL` | Нет | — | Если не задан, rate limiter работает в no-op режиме (fail-open) |
| `SMTP_HOST` | Нет | — | Для отправки email (верификация, сброс пароля) |
| `SMTP_PORT` | Нет | `587` | Порт SMTP |
| `SMTP_USER` | Нет | — | Пользователь SMTP |
| `SMTP_PASSWORD` | Нет | — | Пароль SMTP |
| `SMTP_FROM_EMAIL` | Нет | `noreply@cloudstorage.local` | Адрес отправителя |
| `CORS_ORIGINS` | Нет | `http://localhost:8080` | Разрешённые origins через запятую |
| `FRONTEND_URL` | Нет | `http://localhost:8080` | Базовый URL для ссылок в письмах |
| `FILE_SERVICE_URL` | Нет | `http://file:8000` | Для инвалидации кеша квот при смене плана |

В production сервис **откажется запускаться**, если `JWT_SECRET` или `SERVICE_API_KEY` содержат известные значения-заглушки.

## API Эндпоинты

### Публичные

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/auth/register` | Регистрация нового пользователя |
| `POST` | `/api/auth/login` | Вход по email + пароль |
| `POST` | `/api/auth/refresh` | Обновление access токена (Bearer: refresh токен) |
| `POST` | `/api/auth/forgot-password` | Запрос сброса пароля |
| `POST` | `/api/auth/reset-password` | Сброс пароля по токену |
| `GET` | `/api/auth/verify-email` | Верификация email по токену |

### Аутентифицированные (Bearer токен)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/auth/me` | Получение профиля текущего пользователя |
| `POST` | `/api/auth/plan` | Переключение тарифа (`free` / `pro` / `team`) |
| `POST` | `/api/auth/logout` | Отзыв refresh токена |
| `POST` | `/api/auth/verify-email/request` | Генерация ссылки для верификации email |

### Внутренние (X-API-Key)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/users/{user_id}/quota` | Получение квоты хранилища пользователя (потребляется file-сервисом) |

### Health

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/health` | Liveness-проверка — проверка доступности БД |

## Формат токенов

Access и refresh токены — HS256 JWT со следующими claims:

```json
{
  "sub": "<uuid>",
  "email": "user@example.com",
  "type": "access | refresh",
  "iss": "auth-service",
  "aud": "cloud-storage",
  "exp": 1234567890
}
```

Downstream-сервисы (File, Preview) валидируют `iss` и `aud`, отклоняя токены, выданные для другого стека.

## Rate Limiting

Фиксированные окна (fixed-window) счётчики в Redis. Лимиты по умолчанию:

- **Login**: 10 запросов / минуту на IP
- **Register**: 5 запросов / минуту на IP
- **Password reset**: 3 запроса / минуту на IP

Возвращает `429` с заголовком `Retry-After`. При ошибках Redis — fail-open (запрос проходит).

## Квоты хранилища

| Тариф | Квота |
|---|---|
| `free` | 5 ГБ |
| `pro` | 100 ГБ |
| `team` | 500 ГБ |

При смене тарифа инвалидируется кеш квот file-сервиса через вызов с `X-API-Key`.

## Тестирование

```bash
# Требуется Docker daemon (testcontainers поднимает Postgres 15)
pytest

# Или указать существующую базу данных
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname pytest
```

Тесты используют `testcontainers` для создания эфемерного экземпляра Postgres. Установите `SKIP_TESTCONTAINERS=1`, чтобы пропустить, если Docker недоступен.
