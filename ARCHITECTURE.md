# Архитектура Cloud File Storage

## Обзор

| Параметр | Значение |
|----------|----------|
| Архитектура | Микросервисы с раздельными БД |
| Backend | Python + FastAPI |
| Frontend | React + shadcn/ui + Tailwind CSS |
| API Gateway | Caddy |
| Хранилище | MinIO (S3-совместимое) |
| Базы данных | PostgreSQL (отдельная на сервис) |
| Кэш | Redis 7 |
| Контейнеризация | Docker + Docker Compose |
| Межсервисная коммуникация | REST + API keys |

## Высокоуровневая архитектура

```mermaid
graph TB
    subgraph Client[" "]
        Browser["Браузер"]
    end

    subgraph Gateway["Caddy Gateway :8080"]
        direction TB
        Caddy["reverse proxy + CORS + security headers"]
    end

    subgraph Backend["Backend Services"]
        direction TB
        Auth["Auth Service<br/>FastAPI :8000<br/>JWT, регистрация, квоты"]
        File["File Service<br/>FastAPI :8000<br/>CRUD файлов/папок, корзина"]
        Preview["Preview Service<br/>FastAPI :8000<br/>текстовые превью"]
    end

    subgraph Data["Data Layer"]
        direction TB
        PG_Auth[("PostgreSQL<br/>auth:5433")]
        PG_File[("PostgreSQL<br/>file:5434")]
        MinIO[("MinIO<br/>9000 / 9001")]
        Redis[("Redis<br/>6379")]
    end

    Browser -->|"HTTP :8080"| Caddy
    Caddy -->|"/api/auth/*"| Auth
    Caddy -->|"/api/files/*<br/>/api/folders/*<br/>/api/trash/*<br/>/api/search/*"| File
    Caddy -->|"/api/preview/*"| Preview
    Caddy -->|"/*"| Browser

    Auth --> PG_Auth
    Auth --> Redis
    File --> PG_File
    File --> MinIO
    File --> Redis
    Preview --> PG_Preview
    Preview -.->|"fetch file bytes"| File

    style Client fill:none,stroke:none
    style Gateway fill:#e8f4fd,stroke:#2196F3
    style Backend fill:#e8f8e8,stroke:#4CAF50
    style Data fill:#fff3e0,stroke:#FF9800
```

## Межсервисная коммуникация

```mermaid
graph LR
    subgraph External["Внешние запросы"]
        U["Пользователь"]
    end

    subgraph GW["Caddy Gateway"]
        C["Caddy"]
    end

    A["Auth Service"]
    F["File Service"]
    P["Preview Service"]
    R["Redis"]
    M["MinIO"]
    DB_A[("Auth DB")]
    DB_F[("File DB")]

    U -->|"1. login<br/>POST /api/auth/login"| C
    C --> A
    A -->|"2. validate<br/>credentials"| DB_A
    A -->|"3. rate limit<br/>check"| R
    A -->|"4. return<br/>JWT"| C
    C --> U

    U -->|"5. upload file<br/>POST /api/files/upload<br/>Authorization: Bearer JWT"| C
    C --> F
    F -->|"6. validate JWT<br/>(shared secret)"| A
    F -->|"7. check quota<br/>GET /users/{id}/quota<br/>X-API-Key"| A
    F -->|"8. write object"| M
    F -->|"9. insert record"| DB_F
    F -->|"10. audit log"| DB_F
    C --> U

    U -->|"11. preview<br/>GET /api/preview/{id}<br/>Authorization: Bearer JWT"| C
    C --> P
    P -->|"12. fetch file bytes<br/>GET /api/files/{id}/download<br/>X-API-Key"| F
    P -->|"13. extract text"| P
    C --> U

    style External fill:none,stroke:none
    style GW fill:#e8f4fd,stroke:#2196F3
```

## Поток загрузки файла

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant GW as Caddy Gateway
    participant Auth as Auth Service
    participant File as File Service
    participant Redis as Redis
    participant MinIO as MinIO
    participant DB as File DB

    User->>GW: POST /api/files/upload<br/>Authorization: Bearer JWT
    GW->>File: forward request

    File->>File: 1. decode JWT (shared secret)
    File->>File: 2. sanitize filename (NFKC, block list)
    File->>File: 3. validate extension + MIME
    File->>File: 4. check file size (max 100 MB)

    alt on_conflict=rename
        File->>File: 5. auto-rename: report.pdf -> report (1).pdf
    end

    File->>Redis: 6. check idempotency key
    Redis-->>File: not found (new upload)

    File->>DB: 7. pg_advisory_xact_lock(user_id)
    File->>Auth: 8. GET /users/{user_id}/quota<br/>X-API-Key
    Auth-->>File: {used: 1.2 GB, quota: 5 GB}
    File->>File: 9. check: used + file_size <= quota

    File->>MinIO: 10. put_bytes({user_id}/files/{uuid}.ext)
    MinIO-->>File: ok

    File->>DB: 11. INSERT INTO files
    DB-->>File: ok

    File->>DB: 12. INSERT INTO audit_logs (file.upload)
    File->>Redis: 13. store idempotency key (24h TTL)

    File-->>GW: 201 {id, name, size, ...}
    GW-->>User: 201 Created
```

## Поток скачивания файла

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant GW as Caddy Gateway
    participant File as File Service
    participant DB as File DB
    participant MinIO as MinIO

    User->>GW: GET /api/files/{id}/download
    GW->>File: forward request

    File->>File: 1. decode JWT
    File->>DB: 2. SELECT from files WHERE id and user_id match
    DB-->>File: minio_object_id

    File->>MinIO: 3. get_stream(minio_object_id)
    MinIO-->>File: byte stream

    File-->>GW: 200 StreamingResponse with Content-Disposition
    GW-->>User: file bytes
```

## Поток корзины (soft delete + TTL cleanup)

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant File as File Service
    participant MinIO as MinIO
    participant DB as File DB
    participant Scheduler as APScheduler

    Note over User,Scheduler: Soft Delete
    User->>File: DELETE /api/files/{id}
    File->>MinIO: move files/{uuid}.ext -> trash/{uuid}.ext
    File->>DB: UPDATE files SET deleted_at=now()
    File->>DB: INSERT audit_logs (file.soft_delete)
    File-->>User: 200 {status: "moved_to_trash"}

    Note over User,Scheduler: Restore
    User->>File: POST /api/trash/{id}/restore
    File->>DB: check parent folder is active
    File->>DB: check name conflicts
    File->>DB: UPDATE files SET deleted_at=NULL
    File->>MinIO: move trash/{uuid}.ext -> files/{uuid}.ext
    File-->>User: 200 {status: "restored"}

    Note over User,Scheduler: TTL Cleanup (daily 03:17 UTC)
    Scheduler->>DB: SELECT * FROM files<br/>WHERE deleted_at < now() - 30 days<br/>LIMIT 500
    loop batch (500 rows)
        Scheduler->>MinIO: remove(trash/{uuid}.ext)
        Scheduler->>DB: DELETE FROM files
        Scheduler->>DB: INSERT audit_logs (file.ttl_purge)
    end
```

## Схема базы данных

### Auth Service

```mermaid
erDiagram
    users {
        uuid id PK
        varchar email UK
        varchar hashed_password
        boolean is_active
        boolean is_verified
        timestamp created_at
        timestamp updated_at
        bigint storage_quota
        varchar subscription
        varchar totp_secret
        varchar google_id UK
    }

    verification_tokens {
        uuid id PK
        uuid user_id FK
        varchar token UK
        varchar token_type
        timestamp expires_at
        timestamp created_at
    }

    users ||--o{ verification_tokens : "has tokens"
```

### File Service

```mermaid
erDiagram
    folders {
        uuid id PK
        uuid user_id
        uuid parent_id FK
        varchar name
        text path
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    files {
        uuid id PK
        uuid user_id
        uuid folder_id FK
        varchar name
        bigint size
        varchar mime_type
        varchar minio_object_id
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
        boolean deleted_permanently
    }

    audit_logs {
        uuid id PK
        uuid actor_id
        varchar event
        uuid target_id
        varchar target_kind
        varchar ip
        varchar user_agent
        jsonb extra
        timestamp created_at
    }

    folders ||--o{ folders : "parent"
    folders ||--o{ files : "contains"
    files ||--o{ audit_logs : "audited"
```

## MinIO: структура бакета

```mermaid
graph TB
    subgraph Bucket["cloudstorage bucket"]
        direction TB
        subgraph U1["user_001/"]
            F1["files/uuid1.pdf"]
            F2["files/uuid2.txt"]
            T1["trash/uuid3.jpg"]
        end
        subgraph U2["user_002/"]
            F3["files/uuid4.docx"]
            F4["files/uuid5.png"]
        end
    end

    style Bucket fill:#fff3e0,stroke:#FF9800
```

| Префикс | Назначение | Операции |
|---------|-----------|----------|
| `{user_id}/files/` | Активные файлы | put, get, move, remove |
| `{user_id}/trash/` | Удалённые файлы (30 дней) | get, remove |

## Технологический стек

### Backend

| Компонент | Технология |
|-----------|------------|
| Фреймворк | FastAPI (async) |
| ORM | SQLAlchemy 2.0 + asyncpg |
| Миграции | Alembic |
| Валидация | Pydantic v2 |
| JWT | python-jose (HS256) |
| Email | aiosmtplib + Jinja2 |
| Логирование | structlog |
| MinIO SDK | minio |
| Тесты | pytest + httpx + testcontainers |

### Frontend

| Компонент | Технология |
|-----------|------------|
| Фреймворк | React 18 + Vite |
| UI | shadcn/ui (Radix UI + Tailwind CSS) |
| State | Zustand |
| Роутинг | React Router v6 |
| HTTP | Axios |

### Инфраструктура

| Компонент | Технология |
|-----------|------------|
| Gateway | Caddy 2 |
| БД | PostgreSQL 15 |
| Хранилище | MinIO |
| Кэш | Redis 7 |
| Контейнеры | Docker + Docker Compose |

## Безопасность

### Аутентификация

```mermaid
sequenceDiagram
    participant C as Клиент
    participant A as Auth Service
    participant F as File Service

    C->>A: POST /api/auth/login<br/>{email, password}
    A->>A: bcrypt verify
    A-->>C: {access_token, refresh_token}

    C->>F: GET /api/files/<br/>Authorization: Bearer access_token
    F->>F: decode JWT (shared JWT_SECRET)<br/>verify iss=auth-service, aud=cloud-storage
    F-->>C: 200 OK
```

| Механизм | Реализация |
|----------|-----------|
| User auth | JWT access + refresh токены (HS256) |
| Service-to-service | `X-API-Key` header (общий `SERVICE_API_KEY`) |
| Passwords | bcrypt (passlib) |
| Rate limiting | Redis fixed-window (fail-open) |
| CORS | конкретный origin, не `*` |
| Security headers | X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy |

### Rate Limiting

| Endpoint | Лимит |
|----------|-------|
| Login | 10 req/min на IP |
| Register | 5 req/min на IP |
| Password reset | 3 req/min на IP |
| File upload | 20 req/min на пользователя |
| File delete | 60 req/min на пользователя |
| По умолчанию | 300 req/min на пользователя |

При ошибках Redis — fail-open (запрос проходит).

### Квоты

| Тариф | Квота |
|-------|-------|
| free | 5 ГБ |
| pro | 100 ГБ |
| team | 500 ГБ |

Проверка квоты через `pg_advisory_xact_lock` для атомарности при параллельных загрузках.

## Переменные окружения

| Переменная | Сервис | Обязательна | Описание |
|------------|--------|-------------|----------|
| `JWT_SECRET` | Auth, File | Да | HMAC-секрет для JWT |
| `SERVICE_API_KEY` | Все | Да | Ключ межсервисной коммуникации |
| `REDIS_PASSWORD` | Auth, File | Да | Пароль Redis |
| `POSTGRES_PASSWORD` | Все | Да | Пароль PostgreSQL |
| `MINIO_ROOT_USER` | File | Да | Пользователь MinIO |
| `MINIO_ROOT_PASSWORD` | File | Да | Пароль MinIO |
| `DATABASE_URL` | Каждый | Да | URL подключения к БД сервиса |
| `REDIS_URL` | Auth, File | Нет | URL Redis (fail-open если не задан) |
| `SMTP_HOST` | Auth | Нет | SMTP сервер для email |
| `MINIO_BUCKET` | File | Нет | Имя бакета (по умолчанию `cloudstorage`) |
