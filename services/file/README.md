# File Service

Сервис управления файлами и папками для платформы Cloud File Storage (CFS). Отвечает за загрузку, хранение, перемещение, удаление, поиск и квотирование файлов.

## Содержание

- [Архитектура](#архитектура)
- [Стек](#стек)
- [Структура проекта](#структура-проекта)
- [Быстрый старт](#быстрый-старт)
- [Конфигурация](#конфигурация)
- [Аутентификация](#аутентификация)
- [API Reference](#api-reference)
- [Rate Limiting](#rate-limiting)
- [Обработка ошибок](#обработка-ошибок)
- [Object Key Layout (MinIO)](#object-key-layout-minio)
- [Схема БД](#схема-бд)
- [Тестирование](#тестирование)
- [Деплой](#деплой)
- [Конвенции кода](#конвенции-кода)

---

## Архитектура

```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌──────────┐
│ Frontend│────▶│  Caddy   │────▶│ File       │────▶│ Postgres │
│ (React) │     │ (gateway)│     │ Service    │     │ 15       │
└─────────┘     └──────────┘     │ :8000      │     └──────────┘
                                 │            │     ┌──────────┐
                                 │  ┌──────┐  │────▶│ MinIO    │
                                 │  │Redis │  │     │ (S3)    │
                                 │  └──────┘  │     └──────────┘
                                 └─────┬──────┘
                                       │
                                       ▼
                                 ┌──────────┐
                                 │ Auth     │
                                 │ Service  │
                                 │ :8000    │
                                 └──────────┘
```

**Слои:**
- **API** (`src/api/`) — FastAPI роутеры, маппинг HTTP → service
- **Service** (`src/services/`) — бизнес-логика, domain exceptions
- **Repository** (`src/repositories/`) — все SQL-запросы
- **Model** (`src/models/`) — SQLAlchemy 2.0 ORM
- **Schema** (`src/schemas/`) — Pydantic v2 валидация

---

## Стек

| Компонент | Технология |
|-----------|-----------|
| Framework | FastAPI 0.109 |
| ORM | SQLAlchemy 2.0 (async, Mapped[]) |
| Migrations | Alembic |
| БД | PostgreSQL 15 + asyncpg |
| Хранилище | MinIO (S3-совместимый) |
| Кэш / Rate Limit | Redis 5.0 |
| JWT | python-jose (HS256) |
| Logging | structlog (JSON в production, console в dev) |
| Планировщик | APScheduler (trash TTL cleanup) |
| Валидация | Pydantic v2 + pydantic-settings |
| HTTP клиент | httpx (для Auth service) |

---

## Структура проекта

```
services/file/
├── src/
│   ├── main.py                      # FastAPI app, lifespan, middleware stack
│   ├── config.py                    # Settings (pydantic-settings)
│   ├── exceptions.py                # Доменные исключения
│   ├── scheduler.py                 # APScheduler bootstrap (trash cleanup)
│   ├── models/
│   │   ├── __init__.py              # Engine, Base, get_db, async_session
│   │   ├── file.py                  # File ORM model
│   │   ├── folder.py                # Folder ORM model
│   │   └── audit_log.py            # AuditLog ORM model
│   ├── schemas/
│   │   ├── __init__.py              # Реэкспорт всех схем
│   │   ├── common.py                # ItemResponse, QuotaResponse, Page[T]
│   │   ├── file.py                  # FileResponse, FileUploadResponse, TextPreviewResponse
│   │   ├── folder.py                # FolderCreate, FolderUpdate, FolderResponse
│   │   ├── trash.py                 # TrashItemResponse
│   │   ├── search.py               # SearchResponse
│   │   └── bulk.py                  # BulkDeleteRequest, BulkMoveRequest, BulkOperationResult
│   ├── services/
│   │   ├── file_service.py          # upload, delete, restore, move, rename, bulk ops
│   │   ├── folder_service.py        # CRUD + cycle detection + recursive trash
│   │   ├── quota_service.py         # pg_advisory_xact_lock + Auth quota fetch
│   │   ├── trash_service.py         # list, restore, permanent delete, empty
│   │   ├── search_service.py        # ILIKE search
│   │   ├── audit_service.py         # Best-effort audit log insert
│   │   └── trash_cleanup_service.py # TTL hard-delete (APScheduler cron)
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── file.py                  # FileRepository: all SQL для files
│   │   └── folder.py                # FolderRepository: all SQL для folders
│   ├── api/
│   │   ├── __init__.py              # api_router (агрегация)
│   │   ├── exception_handlers.py    # DomainError → JSON mapping
│   │   ├── files.py                 # /api/files/*
│   │   ├── folders.py               # /api/folders/*
│   │   ├── trash.py                 # /api/trash/*
│   │   ├── search.py                # /api/search/*
│   │   └── health.py                # /health (DB, MinIO, Redis probes)
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── request_id.py            # X-Request-ID generation/propagation
│   │   ├── request_meta.py          # Client IP + User-Agent capture
│   │   ├── access_log.py            # Structured per-request access log
│   │   └── idempotency.py           # Idempotency-Key для upload (Redis)
│   └── utils/
│       ├── dependencies.py          # get_current_user_id (JWT validation)
│       ├── minio_client.py          # Singleton + helpers (put/move/get/stream)
│       ├── validators.py            # sanitize_filename, ext, MIME, Content-Disposition
│       ├── rate_limiter.py          # Redis fixed-window rate limiting
│       ├── cursor.py                # Base64-json cursor pagination
│       ├── conflict.py              # find_available_name, suggest_rename
│       ├── auth_client.py           # HTTP client → Auth /api/users/{id}/quota
│       ├── logging.py               # structlog configuration
│       └── request_meta.py          # ContextVar для IP/UA
├── tests/
│   ├── conftest.py                  # testcontainers PG, FakeMinioStorage, fixtures
│   ├── helpers.py                   # USER_ALICE/USER_BOB, make_jwt
│   ├── test_file_service.py         # 34 интеграционных теста
│   ├── test_phase2.py               # 15 unit тестов (middleware, rate limiter, health)
│   └── __init__.py
├── migrations/
│   ├── env.py
│   └── versions/
│       ├── 0001_initial.py          # pgcrypto, folders, files tables
│       └── 0002_audit_log.py        # audit_logs table
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── pytest.ini
```

---

## Быстрый старт

### Через Docker Compose (рекомендуется)

```bash
# Из корня проекта
docker-compose -f docker-compose.yml up --build
```

Сервис будет доступен на `http://localhost:8002`.

### Локальная разработка

```bash
cd services/file

# 1. Создать виртуальную среду (Python 3.11+)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить миграции
alembic upgrade head

# 4. Запустить сервис
set JWT_SECRET=dev-secret           # Windows
set SERVICE_API_KEY=dev-key
set DATABASE_URL=postgresql+asyncpg://cloudstorage:cloudstorage_secret@localhost:5432/cloudstorage_file
set MINIO_ENDPOINT=localhost:9000
set MINIO_ACCESS_KEY=minioadmin
set MINIO_SECRET_KEY=minioadmin_secret
set REDIS_URL=redis://localhost:6379/0

python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Swagger UI

После запуска доступен по адресу: `http://localhost:8000/docs/file`

---

## Конфигурация

Все настройки задаются через переменные окружения (или `.env` файл).

| Переменная | Обязательна | По умолчанию | Описание |
|-----------|-------------|--------------|----------|
| `ENV` | нет | `development` | `development` / `production` |
| `LOG_LEVEL` | нет | `INFO` | Уровень логирования |
| `DATABASE_URL` | **да** | — | `postgresql+asyncpg://user:pass@host:port/db` |
| `JWT_SECRET` | **да** | — | Общий HS256 секрет с Auth Service |
| `JWT_ISSUER` | нет | `auth-service` | Must match Auth Service |
| `JWT_AUDIENCE` | нет | `cloud-storage` | Must match Auth Service |
| `MINIO_ENDPOINT` | **да** | — | e.g. `minio:9000` |
| `MINIO_ACCESS_KEY` | **да** | — | |
| `MINIO_SECRET_KEY` | **да** | — | |
| `MINIO_BUCKET` | нет | `cloudstorage` | Имя бакета MinIO |
| `MINIO_SECURE` | нет | `false` | HTTPS для MinIO |
| `SERVICE_API_KEY` | **да** | — | Ключ для service-to-service (quota endpoint) |
| `AUTH_SERVICE_URL` | нет | `http://auth:8000` | URL Auth Service |
| `REDIS_URL` | нет | `redis://redis:6379/0` | URL Redis |
| `TRASH_RETENTION_DAYS` | нет | `30` | Дней до hard-delete из trash |
| `TRASH_CLEANUP_CRON` | нет | `17 3 * * *` | Cron для cleanup job |
| `TRASH_CLEANUP_ENABLED` | нет | `true` | Включить cleanup job |
| `MAX_UPLOAD_SIZE` | нет | `104857600` | Лимит загрузки (100 MB) |
| `ALLOWED_MIME_TYPES` | нет | (см. config.py) | Whitelist MIME через запятую |
| `ALLOWED_EXTENSIONS` | нет | (см. config.py) | Whitelist расширений через запятую |
| `DEFAULT_STORAGE_QUOTA` | нет | `5368709120` | Квота по умолчанию (5 GB) |
| `PREMIUM_STORAGE_QUOTA` | нет | `107374182400` | Premium квота (100 GB) |

**Production guard:** в режиме `production` сервис откажется стартовать, если `JWT_SECRET` или `SERVICE_API_KEY` содержат placeholder-значения.

---

## Аутентификация

Все эндпоинты кроме `GET /health` требуют заголовок:

```
Authorization: Bearer <access_token>
```

JWT валидируется по общему секрету с Auth Service:

| Claim | Требование |
|-------|-----------|
| `iss` | `== "auth-service"` |
| `aud` | `== "cloud-storage"` |
| `type` | `== "access"` (refresh токены отклоняются) |
| `sub` | Валидный UUID |

Если токен отсутствует или невалиден, возвращается `401`:
```json
{
  "error": "unauthenticated",
  "detail": "Missing bearer token"
}
```

---

## API Reference

### Files

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/files/` | Список файлов и папок (cursor pagination) |
| `POST` | `/api/files/upload` | Загрузка файла (multipart/form-data) |
| `GET` | `/api/files/quota` | Использование хранилища |
| `GET` | `/api/files/{file_id}` | Метаданные файла |
| `GET` | `/api/files/{file_id}/text-preview` | Текстовый превью (txt/csv/json) |
| `GET` | `/api/files/{file_id}/download` | Скачивание файла (streaming) |
| `POST` | `/api/files/{file_id}/move` | Перемещение в папку |
| `PATCH` | `/api/files/{file_id}/rename` | Переименование |
| `DELETE` | `/api/files/{file_id}` | Мягкое удаление (в trash) |
| `POST` | `/api/files/{file_id}/restore` | Восстановление из trash |
| `DELETE` | `/api/files/{file_id}/permanent` | Безвозвратное удаление |
| `POST` | `/api/files/bulk-delete` | Массовое удаление (до 200) |
| `POST` | `/api/files/bulk-move` | Массовое перемещение (до 200) |

### Folders

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/folders/` | Создание папки |
| `GET` | `/api/folders/` | Список папок (offset pagination) |
| `GET` | `/api/folders/{folder_id}` | Метаданные папки |
| `PATCH` | `/api/folders/{folder_id}` | Обновление (name, parent_id) |
| `DELETE` | `/api/folders/{folder_id}` | Рекурсивное удаление (BFS cascade) |

### Trash

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/trash/` | Список удалённых items |
| `POST` | `/api/trash/{item_id}/restore` | Восстановление |
| `DELETE` | `/api/trash/{item_id}/permanent` | Безвозвратное удаление |
| `POST` | `/api/trash/empty` | Очистка всего trash |

### Search

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/search/?q={query}` | ILIKE поиск по именам файлов/папок |

### Health

| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/health` | Проверка DB, MinIO, Redis (200/503) |

---

### Детали ключевых эндпоинтов

#### POST /api/files/upload

Загрузка файла. Принимает `multipart/form-data`.

**Form fields:**
| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `file` | UploadFile | да | Макс. 100 MB |
| `folder_id` | UUID | нет | Целевая папка |

**Query params:**
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `on_conflict` | `reject\|rename` | `reject` | При коллизии имён |

**Response 201:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "report.pdf",
  "size": 12345,
  "mime_type": "application/pdf"
}
```

**Ошибки:**
- `409` — конфлик имён (содержит `suggested_name`)
- `413` — файл превышает лимит
- `415` — неподдерживаемый тип файла

#### GET /api/files/

Список файлов и папок с cursor-based пагинацией.

**Query params:**
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `folder_id` | UUID | `null` | Папка для списка. `null` = корень |
| `limit` | int (1-1000) | `200` | Макс. items на коллекцию |
| `folders_cursor` | string | `null` | Opaque cursor для папок |
| `files_cursor` | string | `null` | Opaque cursor для файлов |

**Response 200:**
```json
{
  "folders": [
    {
      "id": "uuid",
      "kind": "folder",
      "name": "My Folder",
      "size": 0,
      "mime_type": null,
      "parent_id": "uuid | null",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z | null"
    }
  ],
  "files": [
    {
      "id": "uuid",
      "kind": "file",
      "name": "report.pdf",
      "size": 12345,
      "mime_type": "application/pdf",
      "parent_id": "uuid | null",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z | null"
    }
  ],
  "next_folders_cursor": "base64-string | null",
  "next_files_cursor": "base64-string | null"
}
```

#### POST /api/files/bulk-delete

Массовое мягкое удаление файлов.

**Request:**
```json
{
  "ids": ["uuid1", "uuid2"]
}
```

**Response 200:**
```json
{
  "succeeded": 2,
  "failed": 0,
  "errors": {}
}
```

Максимум 200 ID за запрос (`MAX_BULK_ITEMS`). Каждый ID обрабатывается независимо — ошибка на одном не прерывает остальные.

---

## Rate Limiting

Реализован fixed-window rate limiter через Redis.

| Политика | Лимит | Применяется к |
|----------|-------|---------------|
| `POLICY_UPLOAD` | 20 req/60s | `POST /api/files/upload` |
| `POLICY_DELETE` | 60 req/60s | `DELETE /api/files/{id}`, `DELETE /api/files/{id}/permanent`, `POST /api/files/bulk-delete` |
| `POLICY_DEFAULT` | 300 req/60s | Все остальные эндпоинты |

**Key:** client IP (через `X-Forwarded-For` / `X-Real-IP` / `request.client.host`)

**Response 429:**
```json
{
  "error": "rate_limit_exceeded",
  "detail": "Rate limit exceeded",
  "extra": {
    "retry_after": 30
  }
}
```

При ошибках Redis rate limiter работает в режиме **fail-open** — запросы не блокируются.

---

## Обработка ошибок

Все ошибки возвращаются в формате:

```json
{
  "error": "error_code",
  "detail": "Человекочитаемое описание",
  "extra": {}
}
```

| Error Code | HTTP Status | Описание |
|------------|-------------|----------|
| `unauthenticated` | 401 | Токен отсутствует или невалиден |
| `access_denied` | 403 | Нет прав на ресурс |
| `file_not_found` | 404 | Файл не найден |
| `folder_not_found` | 404 | Папка не найдена |
| `invalid_filename` | 400 | Недопустимое имя файла |
| `unsupported_file_type` | 415 | Тип файла не в whitelist |
| `payload_too_large` | 413 | Файл превышает лимит |
| `quota_exceeded` | 413 | Превышена квота хранилища |
| `cycle_detected` | 409 | Обнаружен цикл в папках |
| `file_name_conflict` | 409 | Конфликт имён файлов |
| `rate_limit_exceeded` | 429 | Превышен лимит запросов |
| `internal_error` | 500 | Внутренняя ошибка сервера |

---

## Object Key Layout (MinIO)

Бакет: `cloudstorage`

```
{user_id}/files/{uuid}{ext}       # Активные файлы
{user_id}/trash/{uuid}{ext}       # Удалённые файлы (soft-deleted)
{user_id}/preview/{uuid}{ext}     # Сгенерированные превью (Preview Service)
```

**Пример:** `550e8400-e29b-41d4-a716-446655440000/files/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf`

При мягком удалении файл перемещается из `files/` в `trash/` (copy + delete). При восстановлении — обратно с новым UUID ключом.

---

## Схема БД

### files

```sql
CREATE TABLE files (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    folder_id           UUID REFERENCES folders(id) ON DELETE SET NULL,
    name                VARCHAR(255) NOT NULL,
    size                BIGINT NOT NULL,
    mime_type           VARCHAR(100),
    minio_object_id     VARCHAR(255) NOT NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE,
    deleted_at          TIMESTAMP WITH TIME ZONE,
    deleted_permanently BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_files_user_id ON files(user_id);
CREATE INDEX idx_files_folder_id ON files(folder_id);
CREATE INDEX idx_files_deleted_at ON files(deleted_at);
```

### folders

```sql
CREATE TABLE folders (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    parent_id   UUID REFERENCES folders(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    path        TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE,
    deleted_at  TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_folders_user_id ON folders(user_id);
CREATE INDEX idx_folders_parent_id ON folders(parent_id);
CREATE INDEX idx_folders_deleted_at ON folders(deleted_at);
```

### audit_logs

```sql
CREATE TABLE audit_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id    UUID NOT NULL,
    event       VARCHAR(100) NOT NULL,
    target_id   UUID,
    target_kind VARCHAR(50),
    ip          VARCHAR(64),
    user_agent  VARCHAR(512),
    extra       JSONB,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_event ON audit_logs(event);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

**Примечание:** `gen_random_uuid()` требует расширение `pgcrypto`. Инициализируется в `init_db()` и в миграции `0001_initial.py`.

---

## Тестирование

### Запуск тестов

```bash
cd services/file

# Все тесты (требуется Docker для testcontainers PostgreSQL)
pytest -q

# Только конкретный файл
pytest tests/test_file_service.py -v

# Только конкретный тест
pytest -k "test_upload_file" -v

# Без Docker (только unit-тесты)
SKIP_TESTCONTAINERS=1 pytest -q
```

### Инфраструктура тестов

| Компонент | Реализация |
|-----------|-----------|
| PostgreSQL | testcontainers `postgres:15-alpine` (session-scoped) |
| MinIO | In-memory `FakeMinioStorage` (monkeypatch) |
| Auth | `app.dependency_overrides[get_current_user_id]` |
| HTTP клиент | `httpx.AsyncClient` + `ASGITransport` |

### Тестовые пользователи

- `USER_ALICE` = `550e8400-e29b-41d4-a716-446655440000`
- `USER_BOB` = `660e8400-e29b-41d4-a716-446655440001`

### Покрытие

- **34 интеграционных теста** — folder CRUD, file upload/list/meta/move/rename/delete, trash, search, quota, auth, IDOR, upload validation, cycles, soft-delete visibility, quota race, download
- **15 unit тестов** — RequestID, RequestMeta, rate limiter, idempotency, health check, structlog, AccessLogMiddleware

### Linting

```bash
ruff check src tests      # Линтер
ruff format src tests     # Автоформатирование
ruff format --check src tests  # Проверка без изменений
```

---

## Деплой

### Docker

```bash
# Сборка образа
docker build -t file-service .

# Запуск
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e JWT_SECRET=... \
  -e SERVICE_API_KEY=... \
  -e MINIO_ENDPOINT=minio:9000 \
  -e MINIO_ACCESS_KEY=... \
  -e MINIO_SECRET_KEY=... \
  file-service
```

### Entrypoint

Dockerfile CMD выполняет:
1. `alembic upgrade head` — применение миграций
2. `uvicorn src.main:app --host 0.0.0.0 --port 8000`

### Middleware Stack (порядок)

```
RequestIDMiddleware        (внешний — генерирует X-Request-ID)
  └─ RequestMetaMiddleware (захватывает IP + User-Agent)
      └─ AccessLogMiddleware (логирует каждый запрос)
          └─ IdempotencyMiddleware (кэширует upload по Idempotency-Key)
              └─ [Routes]
```

### Health Check

`GET /health` проверяет доступность всех зависимостей:

```json
{
  "status": "healthy",
  "service": "file",
  "checks": {
    "database": { "ok": true, "latency_ms": 1.2 },
    "minio": { "ok": true, "latency_ms": 3.4 },
    "redis": { "ok": true, "latency_ms": 0.8 }
  }
}
```

Возвращает `503` при любой нездоровой подсистеме.

---

## Конвенции кода

### Архитектурные правила

1. **API НЕ делает прямой `db.execute`** — только через Service → Repository
2. **Сервисы бросают `DomainError`**, НЕ `HTTPException` — маппинг в `exception_handlers.py`
3. **MinIO только через `src/utils/minio_client.py`** — не использовать `minio.Minio` напрямую
4. **Квота:** `reserve_quota(db, user_id, size)` — advisory lock внутри транзакции, вызывать ДО MinIO upload
5. **JWT:** всегда проверять `type=access` — refresh токены не подходят для data-API

### Валидация

ВСЕГДА перед записью:
- `sanitize_filename` — NFKC нормализация, strip path, NUL/control-chars, Windows reserved, length cap
- `validate_extension` — against `settings.blocked_ext_set` (blacklist: exe, bat, cmd, sh, ps1, msi, com, scr, pif, vbs, js, wsf, cpl, hta, inf, reg, rgs, sct, shb, shs)
- `validate_mime_type` — against `settings.blocked_mime_set` (blacklist: x-msdownload, x-bat, x-cmd, x-sh, x-shellscript, x-executable, x-mach-binary, x-elf)

### Безопасность

- НИКОГДА не возвращать `HTTPException` из сервисов
- НИКОГДА не использовать `file.read()` без лимита — всегда стримить
- НИКОГДА не подставлять `user_id` из request body — только из JWT
- ВСЕГДА проверять `deleted_at IS NULL` в read-запросах
- ВСЕГДА тестировать cross-tenant (IDOR) сценарии
- ВСЕГДА проверять `minio_object_id` на принадлежность `user_id` перед операциями

### Именование

- **Сервисы:** `{resource}_service.py` (file_service, folder_service, trash_service)
- **Репозитории:** `{resource}.py` (file.py, folder.py)
- **Схемы:** `{resource}.py` (file.py, folder.py, trash.py, search.py, bulk.py)
- **Эндпоинты:** RESTful + action suffixes (`/{id}/restore`, `/{id}/permanent`)

### Whitelist

**Blocked extensions:** `exe, bat, cmd, sh, ps1, msi, com, scr, pif, vbs, js, wsf, cpl, hta, inf, reg, rgs, sct, shb, shs`

**Blocked MIME types:** `application/x-msdownload, application/x-bat, application/x-cmd, application/x-sh, text/x-shellscript, application/x-executable, application/x-mach-binary, application/x-elf`

**Previewable extensions:** `pdf, png, jpg, jpeg, gif, webp, txt, csv, json`

**Upload policy:** Blacklist — everything allowed except blocked extensions/MIME types.

### Константы

| Название | Значение |
|----------|---------|
| `MAX_BULK_ITEMS` | 200 |
| `max_upload_size` | 100 MB |
| `stream_chunk_size` | 1 MB |
| `max_filename_length` | 255 bytes UTF-8 |
| `presigned_url_expires` | 900 seconds (15 min) |
| `trash_retention_days` | 30 |
| `_TEXT_PREVIEW_MAX_BYTES` | 256 KB |
| `_MAX_ANCESTOR_HOPS` | 1000 (защита от corrupted trees) |
