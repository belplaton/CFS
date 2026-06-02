# AGENTS.md — Project Memory for Cloud File Storage (CFS)

> Заметки, конвенции и накопленный контекст. Этот файл подхватывается
> opencode автоматически — обновляй его в конце каждой значимой сессии.

---

## 📦 Project Snapshot

**Что:** Аналог Dropbox/Google Drive на микросервисах (MVP, 3 разработчика, ROADMAP 8 нед. апр–май 2026).
**Стек:** FastAPI · PostgreSQL 15 · MinIO · Redis · Caddy · React 18 + shadcn/ui.
**Сервисы:** `auth` (8000, :5433), `file` (8000, :5434), `preview` (8000, :5435) — каждый со своей БД.
**Хранилище:** Единый бакет `cloudstorage` с префиксами `{user_id}/files/`, `{user_id}/trash/`, `{user_id}/preview/`.
**Контракты:** JWT (HS256, общий secret), `X-API-Key` для service-to-service.

**Ключевые документы (в корне):**
- `README.md` — быстрый старт
- `ARCHITECTURE.md` (v2.0) — C3/C4 диаграммы, схемы БД
- `ROADMAP.md` — спринты, milestones
- `docker-compose.yml` — оркестрация
- `.env.example` — все переменные окружения

---

## 🎯 Текущая задача: file-service

**Работаем в:** `services/file/`
**Локальные заметки:** `services/file/AGENTS.md` — детали по сервису, whitelist, конфиги.

### Фазы

| Phase | Статус | Фокус |
|---|---|---|
| **1 — Security & Hardening** | ✅ Все 15 задач | Валидация, JWT, quota race, циклы, presigned URL, streaming |
| **2 — Reliability + Observability (file)** | ✅ 15/15 | Alembic, structlog+request_id, audit log, rate limit, health-check, idempotency, Caddy headers, split schemas, repository pattern, Phase 2 unit tests |
| **3 — Observability + Operations (cross-service)** | ✅ Все 12 задач | UUID PK, Alembic, structlog, health-check, JWT iss/aud/type, repository pattern, rate limiting, exception handlers, **access log middleware** |
| **4 — Фичи и UX-края** | ✅ 6/6 | Recursive trash, TTL cleanup, premium quota, conflict detection, pagination, bulk ops, ~~idempotency~~ |
| **5 — Качество** | 📋 | CI, security tests, load testing, OpenAPI examples |

---

## 🚨 Известные долги (cross-service)

| # | Проблема | Где | Статус | Что делать |
|---|---|---|---|---|
| **1** | ~~Auth Service хранит `user_id = Integer`, File Service — `UUID`~~ | `services/auth/src/models/user.py` ↔ `services/file/src/models/file.py` | ✅ РЕШЕНО в Phase 3 | Auth мигрирован на `Mapped[UUID]`, coerce-код в file `dependencies.py:58` удалён. Breaking change: `UserResponse.id` теперь UUID |
| **2** | ~~Auth service НЕ выдаёт `iss` / `aud` / `type=access` claim-ы в refresh-токенах одинаково~~ | `services/auth/src/utils/security.py` | ✅ РЕШЕНО в Phase 3 | Все токены содержат `iss=auth-service`, `aud=cloud-storage`, `type=access`/`refresh`. File service валидирует все три |
| **3** | ~~File-service не различает free / premium подписку~~ | `services/file/src/services/quota_service.py:get_storage_quota` | ✅ РЕШЕНО в Phase 4.3 | `auth_client.fetch_quota()` ходит в Auth `/api/users/{id}/quota`, 60s TTL cache, fail-open на default |
| **4** | ~~Нет Alembic — схема через `create_all`~~ | `services/file/src/models/__init__.py:init_db` | ✅ РЕШЕНО в Phase 2 | `alembic upgrade head` через Docker entrypoint, lifespan не делает create_all |
| **5** | ~~`declarative_base()` deprecated → `DeclarativeBase`~~ | `services/file/src/models/__init__.py` ↔ `services/auth/src/models/__init__.py` | ✅ РЕШЕНО в Phase 2/3 | `DeclarativeBase` + `Mapped[]` + `mapped_column()` в обоих сервисах |
| **6** | ~~`class Config` deprecated в Pydantic v2 → `ConfigDict`~~ | `services/file/src/config.py` + `services/auth/src/config.py` | ✅ РЕШЕНО в Phase 2/3 | Глобальный рефактор выполнен |
| **7** | Auth service пока не проверяет refresh-токены при logout / revocation list | `services/auth/src/api/auth.py:101-108` | 📋 Phase 5 | Реализовать Redis blacklist + jti claims |
| **8** | В File service не подключён rate limit к /api/files/{id}/rename, /move | `services/file/src/api/files.py` | 📋 Phase 5 | Применить `rate_limit(WRITE)` к PUT/PATCH |
| **9** | **Deviation:** Rate limit использует fixed-window, ROADMAP говорит "token bucket" | `services/file/src/utils/rate_limiter.py:2` | 📋 Документировано | Принято решение: fixed-window достаточно для abuse-stopper; token bucket только если измеренные паттерны покажут burst abuse |

---

## 🛠 Команды

```bash
# Запуск всего стека (Windows)
start.bat

# Только file-service
cd services/file
pip install -r requirements.txt
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Тесты (требуется Docker для testcontainers PostgreSQL)
cd services/file
pytest -q

# Линт / format
ruff check src tests
ruff format src tests
```

---

## 📐 Конвенции кода (file-service)

- **Слои:** API → Service → Model. API НЕ делает прямой `db.execute`.
- **Исключения:** Сервисы бросают `DomainError`, НЕ `HTTPException`. Маппинг в `src/api/exception_handlers.py`.
- **Валидация:** `sanitize_filename` + `validate_extension` + `validate_mime_type` ВСЕГДА перед записью.
- **MinIO:** Только через `src/utils/minio_client.py`. Не использовать `minio.Minio` напрямую.
- **Квота:** `reserve_quota(db, user_id, size)` — берёт advisory lock внутри транзакции. Вызывать ДО MinIO upload.
- **Object keys:** `{user_id}/files/{uuid}{ext}` для активных, `{user_id}/trash/{uuid}{ext}` для soft-deleted.
- **Имена файлов:** Unicode разрешён, NUL/control-chars запрещены, max 255 байт UTF-8.
- **JWT:** Проверять `type=access`! Refresh не подходит для data-API.

---

## 🔒 Безопасность: что НЕЛЬЗЯ нарушать

1. **НИКОГДА** не возвращать `HTTPException` из сервисов. Только `DomainError`.
2. **НИКОГДА** не использовать `file.read()` без лимита. Всегда стримить.
3. **НИКОГДА** не подставлять `user_id` из request body / query — только из JWT.
4. **НИКОГДА** не делать `RedirectResponse` на presigned URL. Только `StreamingResponse` прокси.
5. **НИКОГДА** не сохранять `UploadFile.filename` без `sanitize_filename`.
6. **ВСЕГДА** проверять `deleted_at IS NULL` в read-запросах.
7. **ВСЕГДА** тестировать cross-tenant (IDOR) сценарии.
8. **ВСЕГДА** проверять `minio_object_id` на принадлежность `user_id` перед операциями.

---

## 📝 Whitelist (конфиг)

**MIME:** `image/jpeg, image/png, image/gif, image/webp, image/svg+xml, application/pdf, text/plain, text/csv, application/json, application/msword, docx, xls, xlsx, ppt, pptx, zip, tar, gzip`
**Extensions:** `jpg, jpeg, png, gif, webp, svg, pdf, txt, csv, json, doc, docx, xls, xlsx, ppt, pptx, zip, tar, gz`
**Upload limit:** 100 MB
**Filename max:** 255 байт UTF-8
**Presigned URL expires:** 15 минут
**Folder max depth:** 1000 (защита от corrupted trees)

---

## 🧪 Тестовая инфраструктура

- **PostgreSQL:** testcontainers `postgres:15-alpine` (если Docker доступен; иначе skip)
- **MinIO:** in-memory `FakeMinioStorage` (monkeypatch `src.utils.minio_client`)
- **Auth:** `app.dependency_overrides[get_current_user_id]`
- **Test users:** `USER_ALICE` и `USER_BOB` в `tests/helpers.py`
- **Тестов:** 34 в `tests/test_file_service.py` (auth, IDOR, upload, cycle, soft-delete, quota race)

---

## 🔄 Что обновлять после каждой сессии

1. Чеклист задач (статус completed/in_progress)
2. Новые известные долги (cross-service)
3. Новые конвенции, если вводятся
4. Что осталось на следующую фазу
5. Файл `services/file/AGENTS.md` — если меняется API/конфиг
