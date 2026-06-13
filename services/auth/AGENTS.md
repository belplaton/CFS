# AGENTS.md — Auth Service Local Notes

> Локальный контекст для `services/auth/`. Подхватывается opencode.
> Общий проектный контекст — в `/AGENTS.md`.

---

## 📁 Структура

```
services/auth/
├── src/
│   ├── main.py                       # FastAPI app, lifespan, logging, CORS, exception_handlers
│   ├── config.py                     # Settings (pydantic-settings, ConfigDict)
│   ├── exceptions.py                 # Доменные исключения + RateLimitError
│   ├── models/
│   │   ├── __init__.py               # DeclarativeBase, engine, get_db
│   │   ├── user.py                   # Mapped[UUID] PK
│   │   └── token.py                  # Mapped[UUID], verification_tokens
│   ├── schemas/
│   │   └── __init__.py               # UserCreate, UserLogin, Token, UserResponse (id=UUID), TokenData
│   ├── services/
│   │   └── user_service.py           # CRUD + JWT issuance (iss/aud/type)
│   ├── api/
│   │   ├── __init__.py               # api_router (auth + health)
│   │   ├── auth.py                   # /api/auth/{register,login,me,refresh,forgot,reset,verify}
│   │   ├── health.py                 # GET /health (DB ping)
│   │   ├── users.py                  # GET /api/users/{id}/quota (X-API-Key)
│   │   └── exception_handlers.py     # DomainError → JSON, RateLimitError → 429+Retry-After
│   ├── middleware/
│   │   ├── request_id.py             # X-Request-ID header + structlog binding
│   │   └── access_log.py             # Per-request access logging
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── user.py                   # UserRepository (get_by_id, get_by_email, add, delete)
│   └── utils/
│       ├── security.py               # JWT (iss/aud/type), password hashing
│       ├── dependencies.py           # get_current_user, get_current_verified_user
│       ├── logging.py                # structlog config + get_logger
│       ├── rate_limiter.py           # Redis fixed-window, fail-open (Phase 3.10)
│       └── redis_client.py           # Shared async Redis singleton + null stub
├── alembic.ini
├── migrations/
│   ├── env.py                        # async, URL resolution (ini → env → settings)
│   └── versions/0001_initial.py      # users, verification_tokens, pgcrypto
├── Dockerfile                        # CMD = alembic upgrade head && uvicorn
├── requirements.txt
├── .env.example
└── tests/
    ├── conftest.py
    └── test_*.py
```

---

## 📊 Phase 3 — прогресс (Auth refactor)

| # | Задача | Файл | Статус |
|---|---|---|---|
| 3.1 | Принято решение: user_id Integer→UUID (breaking change) | — | ✅ |
| 3.2 | `DeclarativeBase` миграция User/VerificationToken + UUID PK | `models/{__init__,user,token}.py` | ✅ |
| 3.3 | `ConfigDict` миграция Auth config.py + prod-guard | `config.py` | ✅ |
| 3.4 | Alembic init для Auth: `alembic.ini`, `env.py`, `0001_initial.py` | `migrations/` | ✅ |
| 3.5 | `Dockerfile` CMD = `alembic upgrade head && uvicorn`; `init_db` deprecated | `Dockerfile`, `models/__init__.py` | ✅ |
| 3.6 | structlog + RequestIDMiddleware | `utils/logging.py`, `middleware/request_id.py`, `main.py` | ✅ |
| 3.7 | `GET /health` (DB ping) | `api/health.py` | ✅ |
| 3.8 | JWT claims: `iss=auth-service`, `aud=cloud-storage`, `type=access/refresh` | `utils/security.py` | ✅ |
| 3.9 | Cross-service: File service валидирует iss/aud; убран int→UUID coercion | `file/src/utils/dependencies.py`, `file/src/config.py` | ✅ (file-service) |
| 3.10 | Rate limiting (Redis fixed-window) на `/login`, `/register`, `/forgot-password`, `/reset-password` | `utils/rate_limiter.py`, `utils/redis_client.py`, `api/auth.py` | ✅ |
| 3.11 | Repository pattern: `UserRepository` (static methods) | `repositories/user.py` | ✅ |
| 3.12 | Обновить AGENTS.md (root + этот файл) | `AGENTS.md` | ✅ |
| 3.13 | `ruff check src` | — | ✅ |
| 3.14 | Тесты Phase 3 (auth) | `tests/test_phase3.py` | 📋 (Phase 5) |
| 4.3 | **Premium quota endpoint** для file service | `api/users.py` 🆕, `schemas/__init__.py:QuotaResponse` | ✅ |
| 4.3 | **Premium quota endpoint** для file service | `api/users.py` 🆕, `schemas/__init__.py:QuotaResponse` | ✅ |

**Итог Phase 3:** 13/14 done (3.14 отложен в Phase 5 вместе с общим CI).

---

## 🛠 Команды

```bash
cd services/auth
pip install -r requirements.txt
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Тесты
pytest -q
pytest --asyncio-mode=auto tests/test_phase3.py

# Lint
ruff check src tests
ruff format src tests

# Migrations
alembic current
alembic upgrade head
alembic downgrade -1
alembic history --verbose
```

---

## 📐 Конвенции кода (auth-service)

- **Слои:** API → Service → Repository. API НЕ делает прямой `db.execute` — только через `UserService`.
- **Исключения:** Сервисы бросают `DomainError` (AuthenticationError, UserNotFoundError, UserAlreadyExistsError, RateLimitError, ...). Маппинг в `api/exception_handlers.py`.
- **Repositories:** Static methods, берут `AsyncSession` параметром → участвуют в caller-транзакции.
- **JWT:** `create_access_token` и `create_refresh_token` обязаны передавать `iss=auth-service`, `aud=cloud-storage`, `type=access|refresh`. `decode_token` валидирует все три + `exp` + `sub` (UUID).
- **Rate limiter:** fail-open при недоступности Redis (WARN логируется, request не блокируется).
- **Refresh tokens:** пока НЕ сохраняются в БД (Phase 4 — jti claims + Redis blacklist).
- **CORS:** Default `http://localhost:8080`, переопределяется через `CORS_ORIGINS` (comma-separated). Боевой режим — через Caddy gateway, не напрямую.
- **Secrets:** `JWT_SECRET` и `SERVICE_API_KEY` обязательны; `assert_safe_for_production()` падает на insecure markers в `ENV=production`.

---

## 🔒 Безопасность: что НЕЛЬЗЯ нарушать

1. **НИКОГДА** не возвращать `HTTPException` из сервисов. Только `DomainError`.
2. **НИКОГДА** не подставлять `user_id` из request body / query — только из JWT (`sub`).
3. **НИКОГДА** не делать silent coercion `sub` в int. UUID-строгий.
4. **НИКОГДА** не выдавать токен без `iss`/`aud`/`type` claims.
5. **НИКОГДА** не убирать `WWW-Authenticate: Bearer` на 401/403.
6. **ВСЕГДА** валидировать `iss=auth-service` и `aud=cloud-storage` в `decode_token`.
7. **ВСЕГДА** инвалидировать refresh при logout (Phase 4 — Redis blacklist).
8. **ВСЕГДА** ставить rate limit на /login, /register, /forgot-password, /reset-password.
9. **ВСЕГДА** возвращать одинаковый ответ "If email exists..." на /forgot-password (anti-enumeration).

---

## 🔑 Cross-service контракт (JWT)

Эти значения **должны** совпадать в Auth и File/Preview services:

| Claim | Value | Кто ставит | Кто валидирует |
|---|---|---|---|
| `iss` | `auth-service` | Auth (`create_access_token`, `create_refresh_token`) | File/Preview (`decode_token`) |
| `aud` | `cloud-storage` | Auth | File/Preview |
| `type` | `access` (data) / `refresh` (renew) | Auth | File/Preview |
| `sub` | UUID строкой | Auth | File/Preview (`UUID(sub)`) |
| `exp` | Unix timestamp | Auth (`jose.jwt.encode`) | File/Preview (`require:["exp"]`) |
| `iat` | Unix timestamp | Auth (опционально) | — |

Любой запрос с токеном, не прошедшим эти валидации, отклоняется 401.

---

## ⚙️ Переменные окружения (auth-service)

| Var | Default | Описание |
|---|---|---|
| `ENV` | `development` | `development` / `production`; production-guard |
| `DATABASE_URL` | `postgresql+asyncpg://...:5432/cloudstorage_auth` | Async PG URL |
| `JWT_SECRET` | — (required) | HS256 shared secret; fail-fast в production на insecure |
| `JWT_ALGORITHM` | `HS256` | — |
| `JWT_ISSUER` | `auth-service` | iss claim |
| `JWT_AUDIENCE` | `cloud-storage` | aud claim |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | — |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | — |
| `REDIS_URL` | `None` | `redis://host:6379/0`; если `None` — rate limiter fail-open |
| `CORS_ORIGINS` | `http://localhost:8080` | Comma-separated |
| `SERVICE_API_KEY` | — (required) | X-API-Key для service-to-service |
| `LOG_LEVEL` | `INFO` | structlog level |

---

## 🧪 Тестовая инфраструктура (auth)

- **PostgreSQL:** testcontainers `postgres:15-alpine` (если Docker доступен; иначе skip)
- **Auth client:** `app.dependency_overrides[get_current_user]`
- **Rate limit:** In-memory FakeRedis stub или `monkeypatch` `utils/redis_client.get_redis`
- **Существующие тесты:** `tests/test_auth.py` (старые) + `tests/test_phase3.py` (Phase 3, запланирован)

---

## 🐛 Технические тонкости

### UUID PK + pgcrypto
Auth DB использует `gen_random_uuid()` из pgcrypto. `init_db()` сначала `CREATE EXTENSION IF NOT EXISTS pgcrypto`, затем `create_all` (только для tests). В production — `alembic upgrade head` в Dockerfile entrypoint.

### `decode_token` strict
`python-jose` `decode(token, key, algorithms=[...], audience=..., issuer=...)` — `iss`/`aud` валидируются автоматически. `options={"require": ["exp", "sub", "type"]}` гарантирует, что токены без `type` отвергаются. Затем отдельная проверка `type == "access"` (refresh не принимается в data API).

### Rate limit fail-open
Redis down → `_hit_redis` ловит Exception, логирует `rate_limiter_redis_unavailable` на WARN, возвращается. Запрос проходит. Security trade-off: кратковременная потеря защиты от brute force важнее полного отказа auth.

### DomainError mapping
`install_exception_handlers(app)` в `main.py` регистрирует handler для `DomainError` (catch-all) + конкретные handlers для OpenAPI документации. `RateLimitError` → 429 + `Retry-After: {retry_after}` header.

### Email enumeration
`/forgot-password` всегда возвращает 200 с одним и тем же сообщением, независимо от того, существует ли email. Timing одинаковый (один SELECT + одна ветка).

---

## 🔄 Что обновлять в этом файле

1. Phase 3 прогресс (после каждой подзадачи)
2. Новые cross-service долги (если Auth меняет JWT/API)
3. Новые переменные окружения
4. Изменения в API (новые эндпоинты, breaking changes)

---

## 🛑 Сессия 2026-06-13 — Auth hydration + error handling fixes

**Исправлено:**

1. **Auth hydration** — `onRehydrateStorage` в `auth-store.js` вызывает `refreshProfile()` когда `accessToken` есть в localStorage но `user` равен null. Это предотвращает blank screen после login/refresh.

2. **Error handling** — `login` и `register` actions теперь корректно парсят массивы `detail` из 422 ответов (Pydantic validation errors) в human-readable строки вместо показа `[object Object]`.

3. **Logout** — `logout()` и `resetAuthState()` вызывают `useFileStore.getState().resetData()` для очистки file store state.

4. **AppShell** — добавлен loading guard: если `accessToken` есть но `user` null, показывается loading screen вместо пустого экрана.

**Известные ограничения:**
- `test@test.test` отклоняется Pydantic EmailStr (зарезервированный TLD `.test`). Использовать реальные email для тестов.
