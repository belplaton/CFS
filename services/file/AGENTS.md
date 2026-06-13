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
| Extension | `validate_extension` against `settings.blocked_ext_set` (blacklist) |
| MIME | `validate_mime_type` against `settings.blocked_mime_set` (blacklist) |
| Quota | `pg_advisory_xact_lock(hashtextextended(uid))` + SUM + insert in one txn |
| MinIO ↔ DB | Compensating `minio_client.remove` при сбое DB insert |
| Soft delete | MinIO `copy_object` files/ → trash/ + DB `deleted_at` |
| Restore | MinIO `copy_object` trash/ → files/ (new uuid!) + DB `deleted_at = NULL` |
| Cross-tenant | Все queries с `WHERE user_id = :uid AND deleted_at IS NULL` |
| Folder cycles | BFS по `parent_id` chain, fail-fast |
| JWT | `type=access` + `iss=auth-service` + `aud=cloud-storage` required; `sub` = UUID |
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
| 2.13 | **Cross-service: user_id int↔UUID** — синхронизировать с Auth командой | `dependencies.py` (coerce-код удалён в Phase 3) | ✅ РЕШЕНО в Phase 3 |
| 2.14 | **Cross-service: JWT iss/aud/type=access** — добавить в Auth service | `config.py:jwt_issuer/audience` (default), `dependencies.py` валидирует все три | ✅ РЕШЕНО в Phase 3 |
| 2.15 | Тесты Phase 2: request_id; rate limit; health-check; audit; structlog | `tests/test_phase2.py` 🆕 (11 unit) | ✅ |

**Итог Phase 2:** 15/15 done (после Phase 3 закрыл cross-service долги 2.13/2.14).

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

#### 2.13 Access log middleware (Phase 3)
- `AccessLogMiddleware` эмитит `http.request` structlog-event с `method`, `path`, `status_code`, `duration_ms`, `request_id`, `client_ip`, `user_agent`, `service`.
- Запросы медленнее `slow_request_threshold_ms` (default 1000) эмитятся как `http.request_slow`.
- `/health`, `/docs`, `/redoc`, `/openapi.json` исключены из access log (слишком шумно).
- **Критично:** значения читаются из `request.state.request_id` / `request.state.request_meta`, а не из contextvar. Причина: `BaseHTTPMiddleware` сбрасывает contextvar в finally внутреннего middleware ДО того, как внешний finally прочитает. `request.state` живёт весь request lifecycle.
- Зеркальный middleware в auth-service.

---
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

1. ~~Streaming читает всё в RAM~~ — оставлено (до 100 МБ лимит; multipart отложен в Phase 5).
2. ~~Magic bytes не проверяются~~ — оставлено (Phase 5, `python-magic`).
3. ~~Каскадный soft-delete папок~~ — ✅ РЕШЕНО в Phase 4.1.
4. ~~Quota для premium~~ — ✅ РЕШЕНО в Phase 4.3.
5. ~~Rate limiting~~ — Phase 2.
6. ~~Alembic~~ — Phase 2.
7. ~~Audit log~~ — Phase 2.
8. ~~Access log middleware~~ — Phase 3.

---

## 📊 Phase 4 — прогресс (Фичи и UX-края)

| # | Задача | Файл | Статус |
|---|---|---|---|
| 4.1 | **Recursive trash** — каскадное soft-delete папки + MinIO move для всех файлов в поддереве | `folder_service.py:delete_folder` (BFS по `parent_id`) | ✅ |
| 4.2 | **TTL cleanup** — APScheduler cron hard-delete файлов старше `trash_retention_days` (default 30) | `services/trash_cleanup_service.py` 🆕, `scheduler.py` 🆕 | ✅ |
| 4.3 | **Premium quota** — REST `GET /api/users/{id}/quota` (Auth) + 60s TTL cache + fail-open | `utils/auth_client.py` 🆕, `quota_service.py:get_storage_quota` | ✅ |
| 4.4 | **Conflict detection** — `FileNameConflict` (409) с `suggested_name`; `?on_conflict=rename` auto | `utils/conflict.py` 🆕, `exceptions.py:FileNameConflict` | ✅ |
| 4.5 | **Cursor-based pagination** — base64-json `(name, id)` курсоры, `Page[T]` schema | `utils/cursor.py` 🆕, `schemas/common.py:Page`, `repositories/*:list_in_folder_after` | ✅ |
| 4.6 | **Bulk operations** — `POST /api/files/bulk-delete`, `/bulk-move` (до 200 ids) с per-id error reporting | `schemas/bulk.py` 🆕, `file_service.py:bulk_delete/bulk_move`, `api/files.py` | ✅ |
| 4.7 | Idempotency-Key для upload | `middleware/idempotency.py` | ✅ (Phase 2.10) |

**Итог Phase 4:** 6/6 done (4.7 закрыт в Phase 2).

### Phase 4 — детали реализации

#### 4.1 Recursive trash
- `FolderService.delete_folder` использует BFS через `FolderRepository.list_child_ids` для сбора поддерева (`subtree: list[UUID]`).
- Step 1: BFS по `parent_id` chain, защита от corrupted tree через `_MAX_ANCESTOR_HOPS=1000` (тот же лимит что в cycle detection).
- Step 2: bulk `UPDATE folders SET deleted_at = now() WHERE id IN (subtree)`.
- Step 3: для каждого файла в поддереве — `MinIO copy_object files/ → trash/` (best-effort, при failure остаётся в DB) + `UPDATE files SET deleted_at = now(), minio_object_id = new_key`.
- Audit: один event для root folder + по одному на каждую cascaded папку/файл с `extra={"via_cascade": root_id}`.
- **Orphan safety:** если MinIO move падает, DB всё равно отмечает файл как deleted — TTL cleanup (Phase 4.2) подберёт orphan на следующем тике.

#### 4.2 TTL cleanup
- `services/trash_cleanup_service.py:TrashCleanupService.run_once(now=None, batch_size=500)`.
- Cutoff = `now - settings.trash_retention_days` (default 30 дней).
- Files: SELECT batch WHERE `deleted_at < cutoff AND deleted_permanently = False`, set `deleted_permanently = True`, MinIO remove (best-effort).
- Folders: hard DELETE (без soft-undelete marker; cascade в 4.1 уже обработал файлы).
- Scheduler: `src/scheduler.py:build_scheduler()` — `AsyncIOScheduler` + `CronTrigger.from_crontab(settings.trash_cleanup_cron)` (default `"17 3 * * *"`).
- В `main.py:lifespan` — start на boot, shutdown на stop.
- **Не реализует leader election** — в multi-replica deployment включить coalesce или external lock; DELETE идемпотентен.

#### 4.3 Premium quota
- New endpoint в Auth: `GET /api/users/{user_id}/quota` (`api/users.py`).
- Защищён `X-API-Key` (не user JWT) — service-to-service.
- `User` уже имел `storage_quota` + `used_storage` columns; добавлен `tier` heuristic: `quota > default` → `"premium"`, иначе `"free"`.
- File service: `utils/auth_client.py:fetch_quota(user_id)` — 60s in-memory TTL cache, httpx с 2s timeout, **fail-open** на `settings.default_storage_quota` если Auth недоступен.
- `file_service.upload_file` вызывает `auth_client.invalidate(user_id)` после успешного insert (следующий read увидит свежие цифры).
- Cache scoped to process — multi-replica deployment получает N×60s latency hit на cache miss, что приемлемо.

#### 4.4 Conflict detection
- `exceptions.py:FileNameConflict(409)` с `suggested_name` в `extra` (попадает в 409 body).
- `utils/conflict.py:find_available_name(db, user_id, folder_id, desired)` — один SELECT `SELECT name FROM files WHERE folder_id=?`, потом Python-loop от 1 до 1000 для `(1)`, `(2)`, ...
- `suggest_rename(desired)` — DB-free helper, используется для подсказки в 409 body.
- `?on_conflict=reject|rename` query param (Pydantic `pattern="^(reject|rename)$"`).
- Strip существующего `(N)` суффикса при continuation: `report (1).pdf` + conflict → `report (2).pdf`, не `report (1) (1).pdf`.

#### 4.5 Cursor pagination
- `utils/cursor.py:Cursor(name, id).encode() / .decode()` — base64-urlsafe(json).
- `Page[T] = {items: list[T], next_cursor: str | None}` (Pydantic generic).
- Repository методы `list_in_folder_after(db, ..., cursor, limit)` используют `tuple_(name, id) > (?, ?)` для index-friendly range scan.
- Service `list_*_page(..., limit)` — fetch `limit+1`, если есть лишний — last returned = next cursor.
- `list_files` endpoint теперь возвращает `Page[ItemResponse]`, валидирует cursor через `Cursor.try_decode` (400 на malformed).
- **BREAKING:** `GET /api/files/` ранее возвращал `list[ItemResponse]`, теперь `Page[ItemResponse]`. Клиент-frontend должен обновить парсинг.

#### 4.6 Bulk operations
- `schemas/bulk.py:MAX_BULK_ITEMS=200` — жёсткий cap, выше клиент должен chunk-ить.
- `BulkOperationResult{succeeded, failed, errors: {id: reason}}` — per-id error reporting, не аборт на первой ошибке.
- `file_service.bulk_delete` и `bulk_move` — try/except per id, возвращают `(succeeded, errors)`.
- Endpoints защищены rate limit (`POLICY_DELETE` для delete; move пока без лимита — Phase 5).
- `permanent_delete` НЕ включён в bulk — слишком деструктивно без явного `?force=true`.

---

## 🔄 Что обновлять в этом файле

1. Phase 2 прогресс (после каждой подзадачи)
2. Новые конвенции (имена, паттерны)
3. Известные баги (если появляются)
4. API changes (новые endpoints, изменённые сигнатуры)
5. Whitelist/config изменения

---

## 🛑 Сессия 2026-06-03 — Phase 4 завершена

**Выполнено за сессию:** 6/6 (4.1 Recursive trash, 4.2 TTL cleanup, 4.3 Premium quota, 4.4 Conflict detection, 4.5 Cursor pagination, 4.6 Bulk operations).

**Решения, которые нужно помнить:**

1. **Conflict resolution** — `?on_conflict=reject|rename`. На reject возвращаем 409 с `extra.suggested_name` (DB-free regex hint). На rename используем `find_available_name` с одним SELECT + Python loop до 1000 attempts. Strip существующего `(N)` суффикса для continuation.

2. **Cursor pagination** — base64-urlsafe JSON `{name, id}`. Repository использует `tuple_(name, id) > (?, ?)` для index-friendly range scan. **BREAKING:** `GET /api/files/` теперь возвращает `Page[ItemResponse]`, frontend должен обновить парсинг.

3. **Bulk operations** — per-id try/except, `MAX_BULK_ITEMS=200`. Результат `{succeeded, failed, errors: {id: reason}}`. `permanent_delete` НЕ bulk-friendly (требует `?force=true` — Phase 5).

4. **Recursive trash (4.1)** — BFS по `parent_id` с защитой от corrupted trees (`_MAX_ANCESTOR_HOPS=1000`). MinIO move best-effort (DB = source of truth, TTL reaper подберёт orphan).

5. **TTL cleanup (4.2)** — APScheduler AsyncIOScheduler + CronTrigger. `deleted_permanently=True` ставится ДО MinIO remove (не requeue на следующий tick). Folders hard DB-deleted. Coalesce=True для multi-replica (DELETE идемпотентен). Endpoint `trash_cleanup_enabled` для env-disable в тестах.

6. **Premium quota (4.3)** — Auth `GET /api/users/{user_id}/quota` с X-API-Key gate. `tier` — heuristic `quota > default`. File service: 60s in-memory cache, fail-open на default при недоступности Auth. Cache invalidation в `file_service.upload_file` после успешного insert.

7. **Cross-middleware ContextVar fix (Phase 3, остаётся в силе)** — `RequestID` и `RequestMeta` пишут в `request.state.{request_id,request_meta}` для outer consumers, ContextVars оставлены для service-layer (audit_service). BaseHTTPMiddleware сбрасывает inner ContextVar в finally ДО outer finally читает.

8. **Rate limit fixed-window (deviation)** — оставлено vs ROADMAP "token bucket". Обоснование: для abuse-stopper достаточно, граница окна даёт ≤2×limit на стыке, token bucket нужен только при burst-bandwidth SLA.

**Smoke-test состояние на конец сессии:**
- file: 27 routes, ruff ✅, 15 passed + 34 skipped (testcontainers требует Docker).
- auth: 13 routes, ruff ✅.

**Что осталось на Phase 5:**
- Unit/integration тесты для 4.1–4.6 (по 2-3 на подзадачу, без testcontainers).
- CI pipeline (ruff + pytest + alembic).
- Load testing (upload, bulk, cursor).
- OpenAPI examples.
- Security tests на bulk ops (rate limit, MAX_BULK_ITEMS enforcement).
- `rate_limit(WRITE)` на PUT/PATCH (rename, move) — долг #8.
- Auth logout + Redis revocation list — долг #7.

---

## 🛑 Сессия 2026-06-13 — Upload queue, PDF preview, duplicate name prevention, download fix

**Выполнено за сессию:**

1. **Upload progress widget** — `uploadQueue` state в file-store.js с per-file tracking (progress, status, error). Max 5 параллельных upload через `_processUpload` + `_drainQueue`. `AbortController` для отмены. `UploadProgress.jsx` — fixed bottom-right панель.

2. **PDF preview** — `pdfjs-dist` добавлен в dependencies. `PdfFirstPage` компонент рендерит только страницу 1 через canvas. Worker загружается через Vite `?url` import.

3. **Download 404 fix** — Caddy `@file_api` и `@preview_api`Matchers обновлены с `*/ *` (two-segment wildcards) для маршрутов `/{id}/download`, `/{id}/restore`, `/{id}/permanent`. Корневая причина: `path /api/files/*` матчит только один сегмент.

4. **Duplicate name prevention** — `create_folder` теперь проверяет `FolderRepository.list_existing_names_in_parent` + `FileRepository.list_existing_names_in_folder` перед insert → 409. `rename_folder` и `rename_file` проверяют оба типа. `conflict.py:find_available_name` проверяет обе таблицы.

5. **File move conflict** — `file_service.move_file` и `folder_service.move_folder` проверяют конфликты имён в целевой папке → 409 с `suggested_name`.

6. **Upload policy change** — с whitelist на blacklist. Blocked: `exe, bat, cmd, sh, ps1, msi, com, scr, pif, vbs, js, wsf, cpl, hta, inf, reg, rgs, sct, shb, shs`. Previewable: `pdf, png, jpg, jpeg, gif, webp, txt, csv, json`.

7. **FolderResponse.kind** — добавлено поле `kind: str = "folder"` в схему. Frontend `collectFolders` инжектит `kind: item.kind ?? 'folder'`.

8. **Auth hydration fix** — `onRehydrateStorage` вызывает `refreshProfile()` когда `accessToken` есть но `user` null. AppShell показывает loading screen.

9. **Error handling** — auth-store `login`/`register` теперь парсят массивы `detail` из 422 ответов в строку.

**Smoke-test:** 15/15 PASS.

**Что осталось:**
- Browser testing upload queue, PDF preview, duplicate name prevention.
- `test@test.test` отклоняется Pydantic EmailStr (зарезервированный TLD `.test`). Использовать реальные email для тестов.
