# Архитектура Cloud File Storage

Аналог Dropbox/Google Drive на микросервисах

---

## 📋 Обзор

| Параметр | Значение |
|----------|----------|
| Команда | 3 разработчика |
| Архитектура | Микросервисы с раздельными БД |
| Frontend | React + shadcn/ui + Tailwind CSS |
| Backend | Python + FastAPI |
| API Gateway | Caddy |
| Хранилище файлов | MinIO (единый бакет с префиксами) |
| Базы данных | PostgreSQL (отдельная на сервис) |
| Кэш/очереди | Redis |
| Контейнеризация | Docker (один контейнер на сервис) |
| Развёртывание | Локально через Docker Compose |
| Межсервисная коммуникация | REST + API keys |

### Текущий статус реализации (июнь 2026)

- **Готово и используется в UI:** email/password auth, file CRUD, folders, trash, quota, direct download, browser-native preview для image/PDF/text.
- **Готово на backend, но частично не выведено в UI:** отдельные search/trash/folder endpoints, health probes.
- **Честно не готово:** Google OAuth, TOTP, email verification flow, reset-password confirmation flow, generated previews в отдельном preview-service.
- **Источник истины по текущему состоянию:** `README.md` + `AGENTS.md`. ROADMAP ниже остаётся как исторический план, а не как факт готовности.

---

## 🎯 Функциональность MVP

### Основное
- ✅ Регистрация / авторизация (email + пароль)
- ⚠️ Вход через Google (OAuth2) — не реализован
- ⚠️ Двухфакторная аутентификация (TOTP) — не реализована
- ⚠️ Верификация email — маршрут есть, backend flow не завершён
- ⚠️ Восстановление пароля — только запрос, подтверждение не завершено
- ✅ Загрузка / скачивание / удаление файлов
- ✅ Управление папками (создание, переименование, перемещение)
- ⚠️ Предпросмотр файлов — direct browser preview есть; generated previews через preview-service не включены
- ⚠️ Поиск по имени файла — backend endpoint есть, frontend wiring минимален
- ✅ Корзина (30 дней, с возможностью безвозвратного удаления)
- ✅ Квоты: 5 ГБ (бесплатно), 100 ГБ (подписка)

### Отложено (после MVP)
- ❌ Шаринг файлов по ссылке
- ❌ Совместный доступ по email
- ❌ Версионность файлов
- ❌ Синхронизация в реальном времени (WebSocket)
- ❌ Управление сессиями/устройствами

---

## 🏛️ Микросервисы

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Caddy Gateway                               │
│                         (reverse proxy + CORS)                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Auth Service   │    │  File Service    │    │  Preview Service │
│   (FastAPI)      │◄──►│  (FastAPI)       │◄──►│  (FastAPI)       │
│                  │    │                  │    │                  │
│ - Регистрация    │    │ - Загрузка       │    │ - Генерация      │
│ - Логин          │    │ - Скачивание     │    │   превью         │
│ - JWT            │    │ - Удаление       │    │ - Изображения    │
│ - 2FA (TOTP)     │    │ - Папки          │    │ - PDF            │
│ - OAuth Google   │    │ - Поиск          │    │ - Документы      │
│ - Email verify   │    │ - Корзина        │    │                  │
│ - Reset password │    │ - Квоты          │    │                  │
│ API Key: ✓       │    │ API Key: ✓       │    │ API Key: ✓       │
└──────────────────┘    └──────────────────┘    └──────────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  PostgreSQL      │    │  PostgreSQL      │    │  PostgreSQL      │
│  (auth)          │    │  (file)          │    │  (preview)       │
│  port: 5433      │    │  port: 5434      │    │  port: 5435      │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            MinIO (S3-compatible)                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Bucket: cloudstorage                                           │   │
│  │  Prefixes: {user_id}/files/, {user_id}/trash/, {user_id}/preview/ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            Redis 7                                      │
│  - Кэширование превью                                                   │
│  - Rate limiting для API                                                │
│  - Сессионное хранилище                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

**Межсервисная коммуникация:**
- REST API с аутентификацией через `X-API-Key` header
- Каждый сервис имеет свой API key (общий для всех сервисов)
- Service-to-service запросы идут внутри Docker network

---

## 📁 Структура монорепозитория

```
CloudFileStorage/
├── docker-compose.yml              # Оркестрация всех сервисов
├── docker-compose.dev.yml          # Для локальной разработки
├── .env                            # Переменные окружения
├── .gitignore
├── README.md
├── ARCHITECTURE.md                 # Этот документ
│
├── gateway/                        # Caddy Gateway
│   ├── Caddyfile                   # Конфигурация Caddy
│   └── docker-compose.yml
│
├── services/
│   │
│   ├── auth/                       # Auth Service
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── pyproject.toml
│   │   └── src/
│   │       ├── __init__.py
│   │       ├── main.py             # Точка входа FastAPI
│   │       ├── config.py           # Настройки
│   │       ├── database.py         # Подключение к БД
│   │       ├── models/             # SQLAlchemy модели
│   │       │   ├── __init__.py
│   │       │   ├── user.py
│   │       │   └── session.py
│   │       ├── schemas/            # Pydantic схемы
│   │       │   ├── __init__.py
│   │       │   ├── auth.py
│   │       │   └── user.py
│   │       ├── api/                # API роуты
│   │       │   ├── __init__.py
│   │       │   ├── auth.py
│   │       │   ├── users.py
│   │       │   └── oauth.py
│   │       ├── services/           # Бизнес-логика
│   │       │   ├── __init__.py
│   │       │   ├── auth.py
│   │       │   ├── email.py        # Email рассылка
│   │       │   └── totp.py         # 2FA логика
│   │       └── utils/
│   │           ├── __init__.py
│   │           ├── jwt.py
│   │           └── security.py
│   │
│   ├── file/                       # File Service
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── pyproject.toml
│   │   └── src/
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── config.py
│   │       ├── database.py
│   │       ├── minio.py            # MinIO клиент
│   │       ├── models/
│   │       │   ├── __init__.py
│   │       │   ├── file.py
│   │       │   └── folder.py
│   │       ├── schemas/
│   │       │   ├── __init__.py
│   │       │   └── file.py
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   ├── files.py
│   │       │   ├── folders.py
│   │       │   └── search.py
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── file.py
│   │       │   ├── folder.py
│   │       │   ├── trash.py        # Корзина
│   │       │   └── quota.py        # Лимиты
│   │       └── utils/
│   │           └── validators.py
│   │
│   └── preview/                    # Preview Service
│       ├── docker-compose.yml
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── pyproject.toml
│       └── src/
│           ├── __init__.py
│           ├── main.py
│           ├── config.py
│           ├── minio.py
│           ├── api/
│           │   ├── __init__.py
│           │   └── preview.py
│           └── services/
│               ├── __init__.py
│               ├── image.py        # Превью изображений
│               ├── pdf.py          # PDF превью
│               └── document.py     # Документы (docx, xlsx)
│
├── frontend/                       # React приложение
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/                    # API клиенты
│       ├── components/             # UI компоненты
│       ├── pages/                  # Страницы
│       ├── hooks/                  # Кастомные хуки
│       ├── store/                  # State management (Zustand/Redux)
│       └── utils/
│
└── tests/                          # Общие тесты
    ├── conftest.py
    ├── test_auth/
    ├── test_file/
    └── test_e2e/
```

---

## 🔧 Технологический стек

### Backend (все сервисы)
| Компонент | Технология |
|-----------|------------|
| Фреймворк | FastAPI |
| Валидация | Pydantic v2 |
| ORM | SQLAlchemy 2.0 + asyncpg |
| Миграции БД | Alembic |
| JWT | python-jose или PyJWT |
| OAuth | authlib |
| 2FA | pyotp |
| Email | aiosmtplib + Jinja2 (шаблоны) |
| Тесты | pytest + httpx |
| MinIO SDK | minio |

### Frontend
| Компонент | Технология |
|-----------|------------|
| Фреймворк | React 18 + Vite |
| UI библиотека | shadcn/ui (Radix UI + Tailwind CSS) |
| State management | Zustand (легче Redux) |
| HTTP клиент | Axios или TanStack Query |
| Роутинг | React Router v6 |
| Формы | React Hook Form + Zod |
| Тесты | Vitest + React Testing Library |

### Frontend Design Rules
- Frontend использует визуальный язык **shadcn/ui** с ориентацией на референс `ui.shadcn.com`
- Базовый стиль проекта: **`new-york`**
- Базовая палитра: **`neutral`**
- Темизация строится на semantic CSS variables (`background`, `foreground`, `card`, `muted`, `primary` и т.д.)
- Новые страницы и компоненты должны визуально продолжать существующие shadcn patterns: спокойные surfaces, читаемые card layers, заметные borders, умеренные shadows, простая типографика
- Каждый экран должен иметь явную визуальную иерархию: primary working area, secondary context, вспомогательные actions и предсказуемые interaction states
- Основной критерий качества интерфейса: пользователь за 2-3 секунды понимает, где находится главный фокус и какое действие доступно первым
- Недопустима смесь нескольких визуальных систем внутри одного рабочего сценария; frontend должен оставаться целостным shadcn/ui-first интерфейсом
- Theme layer фронтенда поддерживает режимы `light`, `dark`, `midnight` и `system`; смена темы не должна менять layout-паттерны, только токены и атмосферу интерфейса
- Источник конфигурации для фронтенда: `frontend/components.json`

### Инфраструктура
| Компонент | Технология |
|-----------|------------|
| Gateway | Caddy (автоматический HTTPS) |
| БД | PostgreSQL 15+ |
| Хранилище | MinIO |
| Кэш/очереди | Redis 7 (опционально для MVP) |
| Email (dev) | Mailtrap (100 писем/мес бесплатно) |
| Контейнеры | Docker + Docker Compose |

---

## 🗄️ Схема базы данных

### Auth Service (postgresql://postgres-auth:5432/cloudstorage_auth)

#### Таблица `users`
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP,
    storage_quota   BIGINT DEFAULT 5368709120,
    subscription    VARCHAR(50) DEFAULT 'free',
    totp_secret     VARCHAR(255),
    google_id       VARCHAR(255) UNIQUE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_created_at ON users(created_at);
```

#### Таблица `verification_tokens`
```sql
CREATE TABLE verification_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    token           VARCHAR(255) UNIQUE NOT NULL,
    token_type      VARCHAR(50),
    expires_at      TIMESTAMP NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_verification_tokens_user_id ON verification_tokens(user_id);
CREATE INDEX idx_verification_tokens_token ON verification_tokens(token);
CREATE INDEX idx_verification_tokens_expires_at ON verification_tokens(expires_at);
```

#### Таблица `sessions` (опционально)
```sql
CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token   VARCHAR(255) UNIQUE NOT NULL,
    expires_at      TIMESTAMP NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_refresh_token ON sessions(refresh_token);
```

---

### File Service (postgresql://postgres-file:5432/cloudstorage_file)

#### Таблица `folders`
```sql
CREATE TABLE folders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    parent_id       UUID REFERENCES folders(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    path            TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP,
    deleted_at      TIMESTAMP
);

CREATE INDEX idx_folders_user_id ON folders(user_id);
CREATE INDEX idx_folders_parent_id ON folders(parent_id);
CREATE INDEX idx_folders_deleted_at ON folders(deleted_at);
CREATE INDEX idx_folders_user_parent ON folders(user_id, parent_id);
```

#### Таблица `files`
```sql
CREATE TABLE files (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    folder_id           UUID REFERENCES folders(id) ON DELETE SET NULL,
    name                VARCHAR(255) NOT NULL,
    size                BIGINT NOT NULL,
    mime_type           VARCHAR(100),
    minio_object_id     VARCHAR(255) NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP,
    deleted_at          TIMESTAMP,
    deleted_permanently BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_files_user_id ON files(user_id);
CREATE INDEX idx_files_folder_id ON files(folder_id);
CREATE INDEX idx_files_deleted_at ON files(deleted_at);
CREATE INDEX idx_files_user_folder ON files(user_id, folder_id);
CREATE INDEX idx_files_name ON files(name);
```

#### Таблица `audit_logs` (опционально)
```sql
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID,
    action          VARCHAR(50),
    resource_type   VARCHAR(50),
    resource_id     UUID,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

---

### Preview Service (postgresql://postgres-preview:5432/cloudstorage_preview)

#### Таблица `preview_cache`
```sql
CREATE TABLE preview_cache (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id         UUID NOT NULL,
    preview_type    VARCHAR(50),
    minio_object_id VARCHAR(255),
    expires_at      TIMESTAMP NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_preview_cache_file_id ON preview_cache(file_id);
CREATE INDEX idx_preview_cache_expires_at ON preview_cache(expires_at);
```

---

## 🌐 API Gateway (Caddy)

### Маршрутизация

| Домен/Путь | Сервис |
|------------|--------|
| `api/auth/*` | Auth Service |
| `api/files/*` | File Service |
| `api/preview/*` | Preview Service |
| `/` | Frontend (React) |

### CORS настройки
- `Access-Control-Allow-Origin`: `http://localhost:8080`
- `Access-Control-Allow-Credentials`: `true`
- `Access-Control-Allow-Headers`: `Content-Type, Authorization, X-Requested-With, X-API-Key`

---

## 📦 Docker Compose

### Основные сервисы

| Сервис | Порт | Описание |
|--------|------|----------|
| `gateway` | 8080 | Caddy reverse proxy |
| `postgres-auth` | 5433 | БД Auth Service |
| `postgres-file` | 5434 | БД File Service |
| `postgres-preview` | 5435 | БД Preview Service |
| `minio` | 9000, 9001 | Хранилище файлов |
| `redis` | 6379 | Кэш и rate limiting |
| `auth` | 8000 | Auth Service (внутренний) |
| `file` | 8000 | File Service (внутренний) |
| `preview` | 8000 | Preview Service (внутренний) |

### Переменные окружения

| Переменная | Сервис | Описание |
|------------|--------|----------|
| `SERVICE_API_KEY` | Все | Ключ для межсервисной коммуникации |
| `DATABASE_URL` | Каждый | URL своей БД |
| `REDIS_URL` | File, Preview | Подключение к Redis |
| `MINIO_BUCKET` | File, Preview | Имя бакета MinIO |

---

## 👥 Распределение задач для 3 разработчиков

### Разработчик 1: Auth Service + Frontend Auth UI
- [ ] Auth Service (FastAPI)
- [ ] Регистрация / логин / JWT
- [ ] OAuth Google
- [ ] 2FA (TOTP)
- [ ] Email верификация / восстановление пароля
- [ ] Frontend: страницы входа, регистрации, личного кабинета

### Разработчик 2: File Service + Frontend File UI
- [ ] File Service (FastAPI)
- [ ] Загрузка / скачивание / удаление
- [ ] Управление папками
- [ ] Поиск по файлам
- [ ] Корзина
- [ ] Квоты
- [ ] Frontend: файловый менеджер, загрузка, превью

### Разработчик 3: Preview Service + Инфраструктура
- [ ] Preview Service (FastAPI)
- [ ] Генерация превью (изображения, PDF, документы)
- [ ] Docker Compose оркестрация
- [ ] Caddy настройка
- [ ] MinIO настройка
- [ ] Email интеграция (Mailtrap)
- [ ] Frontend: компонент предпросмотра

---

## 🚀 План разработки (спринты)

### Спринт 1 (1-2 недели): Базовая инфраструктура
- [ ] Настроить монорепозиторий
- [ ] Docker Compose со всеми сервисами
- [ ] PostgreSQL + MinIO + Caddy
- [ ] Базовый Auth Service (регистрация, логин, JWT)
- [ ] Базовый Frontend (форма входа)

### Спринт 2 (2-3 недели): Файловый сервис
- [ ] File Service (загрузка, скачивание, удаление)
- [ ] Управление папками
- [ ] Frontend: файловый менеджер
- [ ] Интеграция с MinIO

### Спринт 3 (1-2 недели): Дополнительные функции
- [ ] Поиск по файлам
- [ ] Корзина (30 дней)
- [ ] Квоты (5 ГБ / 100 ГБ)
- [ ] Preview Service (изображения)

### Спринт 4 (1-2 недели): Улучшения
- [ ] OAuth Google
- [ ] 2FA (TOTP)
- [ ] Email верификация / восстановление пароля
- [ ] Предпросмотр документов и PDF
- [ ] Полировка UI/UX

### Спринт 5 (1 неделя): Тестирование и релиз MVP
- [ ] Интеграционное тестирование
- [ ] Исправление багов
- [ ] Документация
- [ ] Демо

**Итого:** 6-10 недель для MVP

---

## 📝 Следующие шаги

1. **Инициализировать репозиторий**
   ```bash
   git init
   mkdir -p services/{auth,file,preview} gateway frontend tests
   ```

2. **Создать базовый Docker Compose**

3. **Настроить Auth Service** (первый приоритет)

4. **Создать базовый Frontend** с формой входа

---

## 🔒 Безопасность

### Межсервисная аутентификация
- Все сервисы используют общий `SERVICE_API_KEY` для аутентификации
- API key передаётся в заголовке `X-API-Key`
- Сервисы доверяют запросам с валидным API key

### CORS
- Настроен на разрешённые_origin (не `*`)
- `Access-Control-Allow-Credentials: true` требует конкретный origin

### Rate Limiting (планируется)
- Redis-based rate limiting для auth endpoints
- Защита от brute force атак

---

## ❓ Открытые вопросы

- [ ] Нужна ли админка для управления пользователями (изменение квот)?
- [ ] Какой сервис для email выбрать для продакшена (SendGrid / Resend)?
- [ ] Использовать ли WebSocket для real-time обновлений?

---

**Документ создан:** 31 марта 2026  
**Версия:** 2.0 (обновлена архитектура с раздельными БД)

### Изменения в версии 2.0:
- ✅ Разделены базы данных для каждого сервиса
- ✅ Добавлен Redis для кэширования и rate limiting
- ✅ Изменена стратегия MinIO: единый бакет с префиксами
- ✅ Добавлена межсервисная аутентификация (API keys)
- ✅ Исправлены CORS настройки
- ✅ Добавлены индексы для всех таблиц
- ✅ Убрана MinIO Console из публичного доступа
