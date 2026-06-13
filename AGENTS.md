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
**Статус:** MVP готов. Phases 1–4 выполнены. Phase 5 (CI, security/load tests, OpenAPI examples) отложена.

**Ключевые документы (в корне):**
- `README.md` — быстрый старт
- `ARCHITECTURE.md` (v2.0) — C3/C4 диаграммы, схемы БД
- `ROADMAP.md` — спринты, milestones
- `BACKLOG_PASS_1.txt` / `BACKLOG_PASS_2.txt` / `BACKLOG_PASS_3.txt` — текущий интеграционный backlog до честного MVP без mock/demo поведения
- `PASS_1_CONTRACT_MATRIX.txt` — матрица `экран -> store action -> endpoint -> status` для прохода по полной frontend/backend связке
- `PASS_3_RUNBOOK.txt` — Docker/gateway smoke runbook
- `scripts/gateway_smoke.py` — автоматизированный happy-path smoke через `localhost:8080`
- `docker-compose.yml` — оркестрация
- `.env.example` — все переменные окружения

**Gateway / Frontend конвенция:**
- Строгий `Content-Security-Policy: default-src 'none'` и `Cache-Control: no-store` применять только к `/api/*`, не глобально ко всему `:8080`. Для SPA CSP задаётся в `frontend/nginx.conf`, иначе React bundle режется браузером и получается белый экран.
- Gateway обязан проксировать не только `/api/files/*`, но и `/api/folders/*`, `/api/trash/*`, `/api/search/*`; иначе frontend silently упирается во frontend fallback вместо backend.
- Swagger UI через gateway публикуется вне `/api/*` (`/docs/auth`, `/docs/file`, `/docs/preview`), иначе API-only CSP ломает browser docs.

**Frontend / Product reality:**
- `Files` и `Trash` страницы подключены к реальному backend. Mock items больше не источник истины для основного file-manager.
- Runtime mock dataset `frontend/src/data/mock-data.js` удалён; `ROOT_FOLDER_ID` вынесен в нейтральный helper, чтобы demo-модуль не оставался скрытой production-зависимостью.
- Поиск на `Files` странице ходит в реальный `GET /api/search/?q=...` и больше не притворяется локальной фильтрацией текущей папки.
- `Verify email`, `Forgot password`, `Reset password`, `Logout` теперь должны идти через реальные auth endpoints. В development backend возвращает `action_url`/`token` для verify/reset flows, чтобы весь цикл был проходим без SMTP-заглушек.
- В shell/sidebar и на `Security` странице должен отображаться текущий email пользователя из `/api/auth/me`; отсутствие email в UI считать регрессией.
- Auth UX: после успешного verify email и reset password пользователь должен возвращаться на login с явным success notice, а не оставаться на промежуточном техничном экране.
- `Security` и `Billing` остаются status/read-only поверхностями только там, где backend mutation ещё не существует (`TOTP`, billing plan change).
- `2FA` / `backup codes` скрыты из пользовательского MVP surface на `Security` странице до тех пор, пока backend flow не будет реализован end-to-end. Лучше скрывать такие блоки, чем показывать полурабочие CTA.
- Критичный frontend нюанс: `file-store.bootstrap()` нельзя запускать до гидратации `auth-store` из persist/localStorage. Иначе первые `/api/files/*` уйдут без `Authorization`, дадут ложный `Unable to load files`, а после любой навигации “само починится”.
- `Preview Service` держит явные `501 Not Implemented` generated-preview маршруты; browser-native preview для image/PDF/text делается через authenticated file download на frontend.
- `Preview Service` теперь может генерировать текстовые preview для `txt/csv/json/docx/xlsx`, проксируя исходный файл из `file-service` с тем же `Authorization` header. `pdf` и изображения остаются browser-native preview через authenticated download.
- Docker truth: frontend image сейчас собирается через `npm install` и получает `VITE_API_URL` как build arg; `package-lock.json` всё ещё требует отдельной нормализации перед возвратом к `npm ci`. Smoke сценарий для всего стека прогоняется через `python scripts/gateway_smoke.py`.

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

## 📝 Upload Policy (file-service)

**Approach:** Blacklist (everything allowed except blocked).

**Blocked extensions:** `exe, bat, cmd, sh, ps1, msi, com, scr, pif, vbs, js, wsf, cpl, hta, inf, reg, rgs, sct, shb, shs`
**Blocked MIME types:** `application/x-msdownload, application/x-bat, application/x-cmd, application/x-sh, text/x-shellscript, application/x-executable, application/x-mach-binary, application/x-elf`
**Previewable extensions:** `pdf, png, jpg, jpeg, gif, webp, txt, csv, json`
**Upload limit:** 100 MB
**Filename max:** 255 байт UTF-8
**Presigned URL expires:** 15 минут
**Folder max depth:** 1000 (защита от corrupted trees)

**Conflict resolution:** `?on_conflict=reject|rename`. `rename` uses `find_available_name` with `(1)`, `(2)` suffixes.

**Bulk operations:** `POST /api/files/bulk-delete`, `/bulk-move` — до 200 ids, per-id error reporting.

**File move:** `POST /api/files/{id}/move` + `?on_conflict=reject|rename` — checks both files and folders in target.

---

## 🧪 Тестовая инфраструктура

- **PostgreSQL:** testcontainers `postgres:15-alpine` (если Docker доступен; иначе skip)
- **MinIO:** in-memory `FakeMinioStorage` (monkeypatch `src.utils.minio_client`)
- **Auth:** `app.dependency_overrides[get_current_user_id]`
- **Test users:** два фиксированных тестовых пользователя в `tests/helpers.py`
- **Тестов:** 34 в `tests/test_file_service.py` (auth, IDOR, upload, cycle, soft-delete, quota race)

---

## 🔄 Что обновлять после каждой сессии

1. Чеклист задач (статус completed/in_progress)
2. Новые известные долги (cross-service)
3. Новые конвенции, если вводятся
4. Что осталось на следующую фазу
5. Файл `services/file/AGENTS.md` — если меняется API/конфиг

---

## 🧠 Session Notes

- 2026-06-11: `FilesPage` must call `loadFolder(currentFolderId || ROOT_FOLDER_ID)` on mount/current-folder change. Shell bootstrap alone can leave initial `/app/files` view empty until first mutating action refreshes folder contents.
- 2026-06-11: Plain-text preview (`txt/csv/json` when normalized as `preview === "text"`) is safest directly in frontend via authenticated blob download + `blob.text()`. Do not route plain text through preview-service unless there is a strong reason.
- 2026-06-11: Trash restore must fail-open if MinIO object move back from `trash/` to `files/` fails. Keep original `minio_object_id`, clear `deleted_at`, log warning. DB key remains valid, so user restore should not 500 just because object-key relocation failed.
- 2026-06-11: Breadcrumbs in `FileBrowser` should stay visible even at root. Users need a persistent clickable path to return to `My Files`.
- 2026-06-11: `Trash` should be rendered hierarchically using `original_parent_id` / normalized `parentId`, not as one flat root list. Nested deleted files/folders must be browsable with breadcrumbs similar to normal file browsing.
- 2026-06-12: `Content-Disposition` for file downloads must include a valid disposition type (`attachment; ...`). Bare `filename=...` is malformed and can surface in browsers as opaque download/preview network failures.
- 2026-06-12: Plain-text file preview should use dedicated `file-service` JSON endpoint (`/api/files/{id}/text-preview`) rather than download streaming. This avoids browser/XHR transport edge cases on attachment/stream responses.
- 2026-06-13: Duplicate name prevention — both `create_folder` and `rename_folder`/`rename_file` now check both files AND folders for name conflicts before insert/update. Backend returns 409 with `suggested_name`. Frontend `find_available_name` checks both file and folder tables.
- 2026-06-13: File move endpoint `POST /api/files/{id}/move` now checks for name conflicts in target folder before moving. Returns 409 with `suggested_name` on conflict.
- 2026-013: Upload policy changed from whitelist to blacklist approach. Blocked extensions: `exe, bat, cmd, sh, ps1, msi, com, scr, pif, vbs, js, wsf, cpl, hta, inf, reg, rgs, sct, shb, shs`. All other files uploadable.
- 2026-06-13: PDF preview uses client-side `pdfjs-dist` library instead of server-side conversion. Worker loaded via Vite `?url` import. Renders only page 1 in modal for fast preview.
- 2026-06-13: Upload progress widget implemented with queue system. Max 5 concurrent uploads per batch. Uses Zustand `uploadQueue` state with per-file tracking (progress, status, error). `AbortController` for cancellation.
- 2026-06-13: Auth hydration fix — `onRehydrateStorage` in `auth-store.js` calls `refreshProfile()` when `accessToken` exists but `user` is null. AppShell shows loading screen during profile fetch.
- 2026-06-13: Caddy `@file_api` and `@preview_api` matchers updated with `*/ *` (two-segment wildcards) to route `/{id}/download`, `/{id}/restore`, `/{id}/permanent` correctly. Root cause of download 404 bug.
- 2026-06-13: `FolderResponse` schema now includes `kind: str = "folder"` field. Frontend `collectFolders` injects `kind: item.kind ?? 'folder'` so move dialog properly identifies folders.
- 2026-06-13: Error handling in auth-store `login`/`register` improved — `detail` arrays from 422 responses are now properly joined into human-readable strings instead of showing `[object Object]`.
