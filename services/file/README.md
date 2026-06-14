# File Service

Микросервис управления файлами и папками для облачного хранилища CFS (Cloud File Storage). Отвечает за полный жизненный цикл файлов: загрузку, скачивание, организацию, поиск, мягкое удаление (корзину), восстановление и окончательное удаление.

## Стек

| Компонент | Технология |
|---|---|
| Framework | FastAPI (async) |
| ASGI-сервер | Uvicorn |
| База данных | PostgreSQL (SQLAlchemy 2.0 async + asyncpg) |
| Миграции | Alembic |
| Объектное хранилище | MinIO (S3-совместимое) |
| Кэш / Rate-limiting / Идемпотентность | Redis |
| Авторизация | JWT (HS256, разделяется с Auth Service) |
| HTTP-клиент | httpx (межсервисные вызовы) |
| Логирование | structlog (JSON в production, консоль в dev) |
| Фоновые задачи | APScheduler (AsyncIO, cron) |
| Валидация схем | Pydantic v2 + pydantic-settings |

## Структура проекта

```
src/
├── main.py                  # Создание FastAPI приложения, подключение middleware, lifespan
├── config.py                # Все настройки (env-based, pydantic-settings)
├── exceptions.py            # Иерархия доменных исключений
├── scheduler.py             # Инициализация APScheduler для фоновых задач
├── api/
│   ├── __init__.py          # Агрегация роутеров
│   ├── files.py             # CRUD файлов + загрузка + скачивание + bulk-операции
│   ├── folders.py           # CRUD папок
│   ├── trash.py             # Корзина (список / восстановление / удаление / очистка)
│   ├── search.py            # Поиск по ресурсам
│   ├── health.py            # Health check (проверка DB, MinIO, Redis)
│   ├── internal.py          # Межсервисный эндпоинт (инвалидация кэша квоты)
│   └── exception_handlers.py
├── models/
│   ├── __init__.py          # Engine, фабрика сессий, get_db dependency
│   ├── file.py              # ORM-модель File
│   ├── folder.py            # ORM-модель Folder
│   └── audit_log.py         # ORM-модель AuditLog
├── schemas/
│   ├── __init__.py          # Реэкспорт всех схем
│   ├── file.py              # Request/Response схемы для файлов
│   ├── folder.py            # Request/Response схемы для папок
│   ├── common.py            # Общие схемы (ItemResponse, QuotaResponse, Page, DirectoryListingResponse)
│   ├── bulk.py              # Схемы bulk-операций
│   ├── trash.py             # Схема элемента корзины
│   └── search.py            # Схема ответа поиска
├── services/
│   ├── file_service.py      # Бизнес-логика файлов
│   ├── folder_service.py    # Бизнес-логика папок (каскадное удаление/восстановление)
│   ├── trash_service.py     # Оркестрация корзины
│   ├── trash_cleanup_service.py # Автоочистка корзины по TTL
│   ├── search_service.py    # ILIKE-поиск
│   ├── quota_service.py     # Контроль квоты хранилища (advisory locks)
│   └── audit_service.py     # Append-only журнал аудита
├── repositories/
│   ├── file.py              # SQL-запросы для таблицы files
│   └── folder.py            # SQL-запросы для таблицы folders
├── middleware/
│   ├── request_id.py        # Генерация/передача X-Request-ID
│   ├── request_meta.py      # Захват Client IP + User-Agent
│   ├── access_log.py        # Структурированное логирование каждого запроса
│   └── idempotency.py       # Redis-backed Idempotency-Key для POST /api/files/upload
└── utils/
    ├── validators.py        # Санитизация имени файла, валидация расширения/MIME
    ├── dependencies.py      # JWT-зависимость аутентификации (get_current_user_id)
    ├── minio_client.py      # Операции MinIO (put, get, move, remove, presigned URLs)
    ├── rate_limiter.py      # Redis fixed-window rate limiter (FastAPI dependency)
    ├── logging.py           # Конфигурация structlog
    ├── cursor.py            # Base64-URL курсорная пагинация
    ├── conflict.py          # Разрешение конфликтов имени файла (автопереименование)
    ├── request_meta.py      # ContextVar для IP/User-Agent
    └── auth_client.py       # HTTP-клиент к Auth Service (получение квоты, кэширование)
```

## Быстрый старт

### Docker Compose (рекомендуется)

```bash
docker-compose up --build
```

Сервис будет доступен на внутреннем порту `8000` (проксируется через gateway на `http://localhost:8080/api/files`).

### Локальная разработка

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Переменные окружения

| Переменная | Обязательна | По умолчанию | Описание |
|---|---|---|---|
| `ENV` | Нет | `development` | `development` / `production` |
| `DATABASE_URL` | **Да** | — | URL подключения к PostgreSQL |
| `MINIO_ENDPOINT` | **Да** | — | Адрес MinIO сервера |
| `MINIO_ACCESS_KEY` | **Да** | — | Access key MinIO |
| `MINIO_SECRET_KEY` | **Да** | — | Secret key MinIO |
| `MINIO_BUCKET` | Нет | `cloudstorage` | Имя бакета MinIO |
| `REDIS_URL` | Нет | `redis://localhost:6379/0` | URL подключения к Redis |
| `JWT_SECRET` | **Да** | — | Секрет для JWT-токенов |
| `AUTH_SERVICE_URL` | **Да** | — | URL Auth Service для получения квоты |
| `SERVICE_API_KEY` | **Да** | — | Ключ для межсервисных вызовов (`X-API-Key`) |
| `TRASH_CLEANUP_ENABLED` | Нет | `True` | Включить автоочистку корзины |
| `TRASH_TTL_DAYS` | Нет | `30` | Срок хранения в корзине (дни) |
| `MAX_FILE_SIZE_MB` | Нет | `100` | Максимальный размер файла (МБ) |
| `DEFAULT_STORAGE_QUOTA` | Нет | `5368709120` | Квота хранилища по умолчанию (5 ГБ) |
| `PREMIUM_STORAGE_QUOTA` | Нет | `107374182400` | Квота хранилища для premium (100 ГБ) |
| `RATE_LIMIT_DEFAULT` | Нет | `300` | Rate limit по умолчанию (запросов/мин) |
| `RATE_LIMIT_UPLOAD` | Нет | `20` | Rate limit для загрузки (запросов/мин) |
| `RATE_LIMIT_DELETE` | Нет | `60` | Rate limit для удаления (запросов/мин) |

## API Эндпоинты

### Файлы (`/api/files`)

| Метод | Путь | Описание | Rate Limit |
|---|---|---|---|
| `GET` | `/api/files/` | Список папок и файлов в директории с независимыми курсорами | default |
| `POST` | `/api/files/upload` | Загрузка файла (multipart). Параметр `?on_conflict=reject\|rename` | 20/мин |
| `GET` | `/api/files/quota` | Использование хранилища и квота пользователя | default |
| `GET` | `/api/files/{file_id}` | Метаданные файла | default |
| `GET` | `/api/files/{file_id}/text-preview` | UTF-8 превью текстовых файлов (до 256 КБ) | default |
| `GET` | `/api/files/{file_id}/download` | Потоковое скачивание файла | default |
| `POST` | `/api/files/bulk-delete` | Мягкое удаление до 200 файлов за раз | 60/мин |
| `POST` | `/api/files/bulk-move` | Перемещение до 200 файлов в целевую папку | default |
| `DELETE` | `/api/files/{file_id}` | Мягкое удаление файла (в корзину) | 60/мин |
| `POST` | `/api/files/{file_id}/restore` | Восстановление файла из корзины | default |
| `DELETE` | `/api/files/{file_id}/permanent` | Окончательное удаление файла | 60/мин |
| `POST` | `/api/files/{file_id}/move` | Перемещение файла в другую папку | default |
| `PATCH` | `/api/files/{file_id}/rename` | Переименование файла | default |

### Папки (`/api/folders`)

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/folders/` | Создание папки |
| `GET` | `/api/folders/` | Список папок (offset-based) |
| `GET` | `/api/folders/{folder_id}` | Метаданные папки |
| `PATCH` | `/api/folders/{folder_id}` | Обновление имени и/или parent_id |
| `DELETE` | `/api/folders/{folder_id}` | Мягкое удаление папки (каскадно на все вложенные) |

### Корзина (`/api/trash`)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/trash/` | Список всех удалённых элементов (файлы + папки) |
| `POST` | `/api/trash/{item_id}/restore` | Восстановление одного элемента |
| `DELETE` | `/api/trash/{item_id}/permanent` | Окончательное удаление одного элемента |
| `POST` | `/api/trash/empty` | Окончательное удаление всей корзины |

### Поиск (`/api/search`)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/search/?q=...` | Поиск по именам файлов и папок (регистронезависимый, лимит 1-255 символов) |

### Health (`/health`)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/health` | Агрегированный health check (проверка DB, MinIO, Redis). Возвращает 200 или 503 |

### Internal (`/api/internal`)

| Метод | Путь | Описание | Авторизация |
|---|---|---|---|
| `DELETE` | `/api/internal/quota-cache/{user_id}` | Инвалидация кэша квоты пользователя | `X-API-Key` |

## Модели данных

### File

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | Первичный ключ |
| `user_id` | UUID | ID владельца (индекс) |
| `folder_id` | UUID (FK → folders.id) | Родительская папка (nullable, ON DELETE SET NULL) |
| `name` | String(255) | Имя файла |
| `size` | BigInteger | Размер в байтах |
| `mime_type` | String(100) | MIME-тип |
| `minio_object_id` | String(255) | Ключ объекта в MinIO |
| `created_at` | DateTime(tz) | Дата создания |
| `updated_at` | DateTime(tz) | Дата обновления |
| `deleted_at` | DateTime(tz) | Дата мягкого удаления (nullable) |
| `deleted_permanently` | Boolean | Флаг окончательного удаления |

### Folder

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | Первичный ключ |
| `user_id` | UUID | ID владельца (индекс) |
| `parent_id` | UUID (FK → folders.id) | Родительская папка (nullable, ON DELETE CASCADE) |
| `name` | String(255) | Имя папки |
| `path` | Text | Путь (nullable) |
| `created_at` | DateTime(tz) | Дата создания |
| `updated_at` | DateTime(tz) | Дата обновления |
| `deleted_at` | DateTime(tz) | Дата мягкого удаления (nullable) |

### AuditLog

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | Первичный ключ |
| `actor_id` | UUID | ID пользователя (индекс) |
| `event` | String(64) | Тип события (индекс) |
| `target_id` | UUID | ID целевого объекта |
| `target_kind` | String(32) | Тип объекта ("file" / "folder") |
| `ip` | String(64) | IP-адрес клиента |
| `user_agent` | String(512) | User-Agent клиента |
| `extra` | JSONB | Дополнительные данные события |
| `created_at` | DateTime(tz) | Дата события |

## Бизнес-логика

### Загрузка файла

1. Санитизация имени файла (нормализация NFKC, удаление компонентов пути, удаление control-символов, проверка на зарезервированные имена Windows).
2. Валидация расширения по блок-листу (нет `.exe`, `.bat`, `.ps1`, `.dll` и др.).
3. Валидация MIME-типа по блок-листу исполняемых MIME-типов.
4. Проверка размера (по умолчанию максимум 100 МБ).
5. Проверка владения папкой при указании `folder_id`.
6. Разрешение конфликтов имени: `on_conflict=reject` → 409 с предложенным именем; `on_conflict=rename` → автопереименование с суффиксом `(1)`, `(2)` и т.д.
7. Блокировка PostgreSQL advisory lock (`pg_advisory_xact_lock`) на пользователя для сериализации параллельных загрузок и атомарной проверки квоты.
8. Проверка квоты: сумма размеров активных файлов + размер загружаемого файла vs. квота пользователя (из Auth Service, кэш 60 сек).
9. Загрузка байтов в MinIO под уникальным ключом (`{user_id}/files/{uuid}.{ext}`).
10. Вставка записи в БД. При ошибке БД — best-effort очистка объекта MinIO.
11. Запись события аудита (`file.upload`).

### Скачивание файла

1. Поиск файла (активный, принадлежащий пользователю).
2. Потоковая передача объекта MinIO через `StreamingResponse` с заголовками `Content-Disposition` и `Content-Length`.
3. Поддержка UTF-8 имен файлов (RFC 5987).

### Мягкое удаление (корзина)

1. Перемещение объекта MinIO из префикса `files/` в `trash/` (копирование + удаление).
2. Установка `deleted_at = now()` на записи файла.
3. Запись события аудита (`file.soft_delete`).

### Каскадное удаление папок

1. BFS-обход поддерева папок (корень + все вложенные).
2. Пометка всех папок в поддереве как `deleted_at = now()`.
3. Перемещение объектов MinIO активных файлов в `trash/` и пометка записей как удалённых.
4. Запись событий аудита для корневой папки, каждой вложенной папки и каждого файла.
5. Защита от бесконечного цикла (максимальная глубина 1000).

### Восстановление из корзины

1. Сбор всего поддерева удалённых элементов.
2. Проверка активности исходной родительской папки.
3. Проверка конфликтов имён в каждом целевом расположении.
4. Восстановление всех записей папок (`deleted_at = None`).
5. Перемещение объектов файлов из `trash/` обратно в `files/`.

### Фоновые задачи

| Задача | Расписание | Описание |
|---|---|---|
| Автоочистка корзины по TTL | `17 3 * * *` (ежедневно в 03:17 UTC) | Окончательное удаление файлов и папок, находящихся в корзине более 30 дней. Пакетная обработка по 500 записей. Отключается через `trash_cleanup_enabled=False`. |

## Возможности

- **Полный CRUD** для файлов и папок с контролем владения (мульти-тенантность).
- **Иерархическая структура папок** с детекцией циклов при перемещении.
- **Мягкое удаление с корзиной** — все удаления восстанавливаемы; элементы хранятся 30 дней перед автоудалением.
- **Каскадные операции** — удаление/восстановление папок распространяется на все вложенные элементы.
- **Потоковая загрузка и скачивание** — файлы не загружаются целиком в память.
- **Безопасность загрузки** — блокировка исполняемых расширений (50+ паттернов), блокировка MIME-типов, санитизация имён.
- **Контроль квоты хранилища** — PostgreSQL advisory locks для атомарной проверки квоты при параллельных загрузках.
- **Курсорная пагинация** — Base64-URL(JSON) курсоры для стабильной, индекс-дружественной навигации.
- **Bulk-операции** — до 200 файлов за вызов для удаления и перемещения.
- **Разрешение конфликтов имён** — reject с предложением или автопереименование с суффиксом `(N)`.
- **Идемпотентность** — Redis-backed `Idempotency-Key` для POST /api/files/upload (кэш на 24 часа).
- **Rate limiting** — Redis fixed-window: upload (20/мин), delete (60/мин), default (300/мин). Fail-open при ошибках Redis.
- **Поиск** — регистронезависимый ILIKE-поиск по именам файлов и папок.
- **Аудит-логирование** — append-only таблица `audit_logs` для всех действий пользователя.
- **Превью текста** — UTF-8 превью для текстовых/CSV/JSON файлов (до 256 КБ).
- **Presigned URL** — краткосрочные (15 мин) presigned URL для прямого доступа к MinIO.
- **Health check** — проверка доступности DB, MinIO и Redis с отображением задержки.
- **Межсервисная авторизация** — внутренний эндпоинт с `X-API-Key` для инвалидации кэша квоты.
- **Структурированное логирование** — JSON в production, человекочитаемое в development; request ID传播 через весь запрос.

## Тестирование

```bash
pytest
```

Тесты используют `pytest-asyncio` с автоматическим режимом и `testcontainers` для PostgreSQL.

## Обработка ошибок

Сервис использует разделение между доменными и HTTP-схемами:

- **Доменные исключения** (`src/exceptions.py`) — иерархия с `DomainError` в корне:
  - `AuthenticationError` (401)
  - `AccessDenied` (403)
  - `FileNotFound` / `FolderNotFound` (404)
  - `InvalidFileName` (400)
  - `UnsupportedFileType` (415)
  - `PayloadTooLarge` / `QuotaExceeded` (413)
  - `CycleDetected` / `ConflictError` / `FileNameConflict` (409)
  - `RateLimitExceeded` (429, с `Retry-After`)

- **Централизованная обработка** — единая точка регистрации маппинга исключений → JSON-ответ:
  ```json
  {"error": "code", "detail": "human message", "extra": {...}}
  ```

- **Философия fail-open** — ошибки Redis, MinIO, Auth Service и аудита логируются, но не блокируют основную операцию пользователя.
