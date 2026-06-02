# AGENTS.md — File Service Local Notes

> Локальный контекст для `services/file/`. Подхватывается opencode.
> Общий проектный контекст — в `/AGENTS.md`.

---

## 📁 Структура

```
services/file/
├── src/
│   ├── main.py                      # FastAPI app, lifespan, logging
│   ├── config.py                    # Settings (pydantic-settings)
│   ├── exceptions.py                # Доменные исключения
│   ├── models/
│   │   ├── __init__.py              # Engine, Base, init_db (Phase 2 → Alembic)
│   │   ├── file.py
│   │   └── folder.py
│   ├── schemas/
│   │   └── __init__.py              # Все Pydantic схемы (Phase 2 → split)
│   ├── services/
│   │   ├── file_service.py          # upload, delete, restore, move, rename
│   │   ├── folder_service.py        # CRUD + cycle detection
│   │   ├── quota_service.py         # pg_advisory_xact_lock + SUM
│   │   ├── trash_service.py         # list, empty
│   │   └── search_service.py        # ILIKE search
│   ├── api/
│   │   ├── __init__.py              # api_router
│   │   ├── exception_handlers.py    # DomainError → JSON
│   │   ├── files.py                 # /api/files/*
│   │   ├── folders.py               # /api/folders/*
│   │   ├── trash.py                 # /api/trash/*
│   │   └── search.py                # /api/search/*
│   └── utils/
│       ├── dependencies.py          # get_current_user_id (JWT)
│       ├── minio_client.py          # Singleton + helpers (put/move/get/stream)
│       └── validators.py            # sanitize_filename, ext, MIME, RFC 5987
├── tests/
│   ├── conftest.py                  # testcontainers PG, fake MinIO
│   ├── helpers.py                   # USER_ALICE/BOB, make_jwt
│   ├── test_file_service.py         # 34 теста
│   ├── __init__.py
├── pytest.ini
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## 🔐 Security Boundaries

| Граница | Защита |
|---|---|
| Upload (Content-Length) | Stream по `stream_chunk_size`, abort при `> max_upload_size` |
| Filename | `sanitize_filename` (NFKC, strip path, drop NUL, win-reserved) |
| Extension | `validate_extension` against `settings.allowed_ext_set` |
| MIME | `validate_mime_type` against `settings.allowed_mime_set` |
| Quota | `pg_advisory_xact_lock(hashtextextended(uid))` + SUM + insert in one txn |
| MinIO ↔ DB | Compensating `minio_client.remove` при сбое DB insert |
| Soft delete | MinIO `copy_object` files/ → trash/ + DB `deleted_at` |
| Restore | MinIO `copy_object` trash/ → files/ (new uuid!) + DB `deleted_at = NULL` |
| Cross-tenant | Все queries с `WHERE user_id = :uid AND deleted_at IS NULL` |
| Folder cycles | BFS по `parent_id` chain, fail-fast |
| JWT | `type=access` required; `iss`/`aud` если заданы |
| Download | `StreamingResponse` прокси, `Content-Disposition: filename*=UTF-8''...` |

---

## 🧪 Команды

```bash
# Запуск с тестовыми env (envs из conftest.py, JWT_SECRET=pytest-...)
cd services/file
pip install -r requirements.txt
pytest -q                          # 34 теста, нужны testcontainers + Docker
pytest -q -k "test_upload"         # только upload-тесты
SKIP_TESTCONTAINERS=1 pytest -q    # skip, если Docker недоступен

# Локальный запуск против реального Postgres
DATABASE_URL=postgresql+asyncpg://cloudstorage:cloudstorage_secret@postgres-file:5432/cloudstorage_file \
JWT_SECRET=dev-secret \
SERVICE_API_KEY=dev-key \
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🗂 DB Schema (текущая, без Alembic)

```sql
-- File Service: cloudstorage_file
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

**Note:** `gen_random_uuid()` требует `pgcrypto` — инициализируется в `init_db()` через `CREATE EXTENSION IF NOT EXISTS pgcrypto`.

---

## 📊 Phase 1 — что сделано

✅ Все 15 задач security hardening. Закрыты: race condition в квоте, path traversal, MIME whitelist, soft delete visibility, folder cycles, refresh token в data API, MinIO redirect leak, compensating delete, pgcrypto.

Подробности: `/AGENTS.md` (общий) + git log.

---

## 📊 Phase 2 — прогресс (Reliability + Observability)

| # | Задача | Файл | Статус |
|---|---|---|---|
| 2.1 | **Alembic init** | `alembic.ini`, `migrations/env.py`, `migrations/versions/0001_initial.py` | ✅ |
| 2.2 | Удалить `create_all` из `models/__init__.py`, вызывать `alembic upgrade head` в entrypoint (Dockerfile CMD) | `models/__init__.py`, `main.py`, `Dockerfile` | ✅ |
| 2.3 | `DeclarativeBase` миграция (SQLAlchemy 2.0) | `models/{__init__,file,folder}.py` | ✅ |
| 2.4 | `ConfigDict` миграция (Pydantic v2) | `config.py`, `schemas/{__init__,file,folder,trash,common}.py` | ✅ |
| 2.5 | **Structured logging** (structlog) с `request_id` middleware | `utils/logging.py` 🆕, `middleware/request_id.py` 🆕, `main.py` | ✅ |
| 2.6 | **Audit log table + запись** | `models/audit_log.py` 🆕, `services/audit_service.py` 🆕, `migrations/versions/0002_audit_log.py` 🆕, вызовы в `file_service` и `folder_service` | ✅ |
| 2.7 | **Rate limiting** через Redis (fixed-window INCR+EXPIRE, upload/delete) | `utils/rate_limiter.py` 🆕, dependency в `api/files.py` | ✅ |
| 2.8 | **Caddy security headers** (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, CSP, COOP/CORP, Permissions-Policy) | `gateway/Caddyfile` | ✅ |
| 2.9 | **Health-check** с проверкой зависимостей (DB, MinIO, Redis); 200/503 | `api/health.py` 🆕 | ✅ |
| 2.10 | **Idempotency-Key** для upload (Redis cache, body fingerprint, 409 on mismatch) | `middleware/idempotency.py` 🆕 | ✅ |
| 2.11 | Split schemas: `schemas/{file,folder,trash,search,common}.py` | `schemas/` | ✅ |
| 2.12 | Repository pattern: `FileRepository` + `FolderRepository`; все DB queries в `repositories/` | `repositories/` 🆕 | ✅ |
| 2.13 | **Cross-service: user_id int↔UUID** — синхронизировать с Auth командой | `dependencies.py` (уже есть fallback с WARNING) | 📋 (XL) |
| 2.14 | **Cross-service: JWT iss/aud/type=access** — добавить в Auth service | `auth/utils/security.py` | 📋 (XL) |
| 2.15 | Тесты Phase 2: request_id; rate limit; health-check; audit; structlog | `tests/test_phase2.py` 🆕 (11 unit) | ✅ |

**Итог Phase 2:** 13/15 done, осталось 2.13/2.14 (XL, требует команду Auth).

#### 2.12 Repository pattern
- `src/repositories/__init__.py` реэкспортит `FileRepository` и `FolderRepository`.
- `FileRepository` методы: `get_active`, `get_any_state`, `get_trashed`, `list_in_folder`, `list_trashed`, `search_by_name`, `add`, `delete`.
- `FolderRepository` методы: `get_active`, `list_in_folder`, `list_trashed`, `search_by_name`, `get_parent_id`, `add`, `delete`.
- Все статические, берут `AsyncSession` параметром → участвуют в caller-транзакции.
- `services/file_service.py`, `services/folder_service.py`, `services/trash_service.py`, `services/search_service.py` — все `db.execute(select(...))` заменены на вызовы repositories.
- Никаких `from sqlalchemy import select` в `services/` кроме одной строки, которая была заменена на `FileRepository.get_trashed`.

### Phase 2 — детали реализации

#### 2.5 Structured logging
- `structlog==24.1.0` настроен в `utils/logging.py` (production = JSON, dev = console).
- `RequestIDMiddleware` принимает входящий `X-Request-ID` или генерирует `uuid4().hex`; эхо в response.
- `RequestMetaMiddleware` записывает client IP (X-Forwarded-For leftmost) и User-Agent в `ContextVar`.
- Все логгеры мигрированы с stdlib `logging` на `structlog.get_logger`/`get_logger(__name__)`.
- Сообщения используют `event.subevent`-style (например, `file.uploaded`, `quota.exceeded`).

#### 2.6 Audit log
- Таблица `audit_logs` (0002_audit_log): `actor_id`, `event`, `target_id`, `target_kind`, `ip`, `user_agent`, `extra` (JSONB), `created_at`.
- `services/audit_service.record_event()` обёрнут в try/except (SQLAlchemyError) — failure НЕ блокирует user request, но логируется WARN.
- IP/UA берутся автоматически из `RequestMetaMiddleware` ContextVar.
- Записываемые события: `file.upload`, `file.soft_delete`, `file.restore`, `file.permanent_delete`, `file.move`, `file.rename`, `folder.create`, `folder.rename`, `folder.move`, `folder.soft_delete`, `trash.empty`.

#### 2.7 Rate limiting
- `utils/rate_limiter.py`: fixed-window INCR+EXPIRE в pipeline (атомарно).
- Политики: `POLICY_UPLOAD=20/min`, `POLICY_DELETE=60/min`, `POLICY_DEFAULT=300/min`.
- Fail-open на Redis errors (WARN логируется).
- Применён к `POST /api/files/upload` и `DELETE /api/files/{id}` + permanent.

#### 2.9 Health-check
- `/health` пробует DB (`SELECT 1`), MinIO (`bucket_exists`), Redis (`ping`).
- 200 + per-probe JSON когда всё ok, 503 + детали когда что-то падает.
- Probe-failure логируется WARN с подсистемой.

#### 2.10 Idempotency
- `IdempotencyMiddleware` — POST /api/files/upload, кэширует `(status, body, fingerprint)` в Redis 24h.
- На повторе: возвращает кэшированный ответ (200); на body mismatch: 409 Conflict.
- Fingerprint = `sha256(body)`. Ключ = `idemp:{user_id}:{key}`.

---

## 🐛 Технические тонкости

### `get_db` и транзакции
`get_db` использует `session.commit()` в finally. Это означает, что **все** операции внутри endpoint'а — в одной outer-транзакции. Advisory lock берётся внутри неё и освобождается при commit/rollback. Это правильное поведение, но при рефакторе нужно помнить.

### `expire_on_commit=False`
Engine создаётся с `expire_on_commit=False` — атрибуты SQLAlchemy-модели не сбрасываются после commit. Это упрощает использование row после flush, но требует явного `await session.refresh(obj)` если нужны DB-defaults (например, `created_at`).

### Streaming upload
Phase 1 читает весь файл в память (`b"".join(chunks)`) — это OK для лимита 100 МБ. Для большего — Phase 4 введёт multipart upload в MinIO (SDK поддерживает `put_object` с chunked upload).

### MinIO move vs upload+delete
`copy_object` + `remove_object` в MinIO — атомарны *внутри MinIO* (есть `copy` API, но нет `rename` в S3). Между MinIO и БД — eventual consistency. Если DB упал после copy — есть orphan в новом месте. Для MVP это OK (orphan reaper в Phase 4).

### `gen_random_uuid()` vs Python uuid4
Мы полагаемся на `gen_random_uuid()` из pgcrypto — это даёт UUID v4. Если pgcrypto не установлен — INSERT упадёт. В `init_db()` сначала `CREATE EXTENSION`, потом `create_all`.

---

## 🚧 Известные ограничения Phase 1

1. **Streaming читает всё в RAM** (до 100 МБ). Phase 4 — multipart.
2. **Magic bytes не проверяются** — `content_type` берётся из заголовка. Phase 4 — `python-magic`.
3. **Каскадный soft-delete папок** — не реализован. Phase 4.
4. **Quota для premium** — Phase 4 (запрос к Auth).
5. **Multipart upload** — Phase 4.
6. **Rate limiting** — Phase 2.
7. **Alembic** — Phase 2.
8. **Audit log** — Phase 2.
9. **Magic-bytes / контент-sniffing** — Phase 4.

---

## 🔄 Что обновлять в этом файле

1. Phase 2 прогресс (после каждой подзадачи)
2. Новые конвенции (имена, паттерны)
3. Известные баги (если появляются)
4. API changes (новые endpoints, изменённые сигнатуры)
5. Whitelist/config изменения
