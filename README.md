# ☁️ Cloud File Storage

Аналог Dropbox/Google Drive на микросервисах

## 📋 Описание

Проект представляет собой облачное хранилище файлов с микросервисной архитектурой.

### Текущий статус (июнь 2026)
- ✅ Регистрация / авторизация (email + пароль)
- ✅ Загрузка / скачивание / удаление файлов
- ✅ Управление папками (создание, переименование, перемещение, рекурсивное удаление)
- ✅ Корзина (soft delete, restore, permanent delete, TTL cleanup 30 дней)
- ✅ Квоты и отображение usage в UI (free / premium)
- ✅ Поиск по имени файлов через backend
- ✅ Конфликт имён при загрузке/создании/переименовании/перемещении (reject|rename)
- ✅ Bulk операции (удаление, перемещение до 200 файлов)
- ✅ Cursor-based пагинация
- ✅ Browser-native preview для image / PDF (pdfjs-dist, первая страница)
- ✅ Text preview для txt/csv/json/docx/xlsx через preview-service
- ✅ Upload progress widget с очередью (макс. 5 параллельных)
- ✅ Audit log + structured logging (structlog)
- ✅ Rate limiting (Redis fixed-window)
- ✅ Health check endpoints (DB, MinIO, Redis probes)
- ⚠️ Billing UI показывает текущую квоту, но не меняет план на backend
- ❌ Google OAuth
- ❌ 2FA (TOTP)
- ❌ Email verification flow (backend готов, frontend не подключён)
- ❌ Reset-password confirmation flow (backend готов, frontend не подключён)
- ❌ Shared file links
- ❌ Real-time sync (WebSocket)
- ❌ CI pipeline, security tests, load testing (Phase 5, отложена)

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        Caddy Gateway (8080)                      │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ Auth Service  │      │ File Service  │      │Preview Service│
│   (FastAPI)   │      │   (FastAPI)   │      │   (FastAPI)   │
│    port 8000  │      │    port 8000  │      │    port 8000  │
└───────────────┘      └───────────────┘      └───────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  PostgreSQL  │      │  PostgreSQL  │      │  PostgreSQL  │
│  (auth:5433) │      │  (file:5434) │      │(preview:5435)│
└──────────────┘      └──────────────┘      └──────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────┐
        │    MinIO     │ │    Redis     │ │ Frontend │
        │ (9000, 9001) │ │    (6379)    │ │  (8080)  │
        └──────────────┘ └──────────────┘ └──────────┘
```

**Ключевые изменения:**
- Каждый сервис имеет свою базу данных
- Redis для кэширования и rate limiting
- MinIO: единый бакет с префиксами пользователей
- API keys для межсервисной коммуникации

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd CloudFileStorage
```

### 2. Настройка переменных окружения

```bash
# Скопируйте пример файла окружения
cp .env.example .env

# Отредактируйте .env при необходимости (опционально)
```

### 3. Запуск проекта

**Вариант для Windows (рекомендуется):**

```bash
# Просто запустите скрипт - он всё сделает сам!
start.bat
```

Скрипт автоматически:
1. Проверит наличие собранного frontend
2. Соберёт React приложение (если нужно)
3. Запустит все сервисы

**Вариант для Linux/Mac:**

```bash
docker compose up -d --build
```

### 4. Остановка проекта

**Windows:**
```bash
stop.bat
```

**Linux/Mac:**
```bash
docker-compose down
```

### 4.1 Smoke через gateway

После старта стека:

```bash
python scripts/gateway_smoke.py
```

Скрипт ходит только через `http://localhost:8080` и проверяет:
- health endpoints
- register/login/me
- verify email
- create folder
- upload/search/download
- trash/restore/permanent delete
- forgot-password/reset-password
- logout + refresh revoke

### 5. Проверка работы

| Сервис | URL | Описание |
|--------|-----|----------|
| **Frontend** | http://localhost:8080 | Веб-интерфейс |
| **Auth Service** | http://localhost:8080/api/auth/ | API аутентификации |
| **File Service** | http://localhost:8080/api/files/ | API файлов |
| **Folder API** | http://localhost:8080/api/folders/ | API папок |
| **Trash API** | http://localhost:8080/api/trash/ | API корзины |
| **Search API** | http://localhost:8080/api/search/ | API поиска |
| **Preview Service** | http://localhost:8080/api/preview/ | API превью |
| **Health Check** | http://localhost:8080/health | Deep health file-service |
| **Auth Health** | http://localhost:8080/health/auth | Проверка Auth Service |
| **File Health** | http://localhost:8080/health/file | Проверка File Service |
| **Preview Health** | http://localhost:8080/health/preview | Проверка Preview Service |
| **Auth DB** | localhost:5433 | PostgreSQL (Auth Service) |
| **File DB** | localhost:5434 | PostgreSQL (File Service) |
| **Preview DB** | localhost:5435 | PostgreSQL (Preview Service) |
| **MinIO Console** | http://localhost:9001 | Консоль MinIO (только локально) |
| **Redis** | localhost:6379 | Redis |

### 6. API Документация

Каждый сервис предоставляет Swagger UI через gateway:

- Auth Service: http://localhost:8080/docs/auth
- File Service: http://localhost:8080/docs/file
- Preview Service: http://localhost:8080/docs/preview

### 6.1 CI и Docker truth

- Frontend Docker build теперь использует `VITE_API_URL` как build-arg, а не только runtime env.
- Базовый CI лежит в `.github/workflows/ci.yml` и гоняет frontend tests/build плюс backend pytest для `auth` и `file`.
- Подробный ручной сценарий проверки лежит в `PASS_3_RUNBOOK.txt`.

## 📁 Структура проекта

```
CloudFileStorage/
├── docker-compose.yml          # Оркестрация всех сервисов
├── .env                        # Переменные окружения
├── .env.example                # Пример переменных
├── ARCHITECTURE.md             # Подробная архитектура
├── README.md                   # Этот файл
│
├── gateway/                    # Caddy Gateway
│   └── Caddyfile
│
├── services/
│   ├── auth/                   # Auth Service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── src/
│   │
│   ├── file/                   # File Service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── src/
│   │
│   └── preview/                # Preview Service
│       ├── Dockerfile
│       ├── requirements.txt
│       └── src/
│
└── frontend/                   # React приложение
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    └── src/
```

## 🛠️ Разработка

### Запуск отдельного сервиса (для разработки)

```bash
# Auth Service
cd services/auth
docker-compose up --build

# File Service
cd services/file
docker-compose up --build

# Preview Service
cd services/preview
docker-compose up --build

# Frontend
cd frontend
npm install
npm run dev
```

### Переменные окружения

Основные переменные в `.env`:

```bash
# PostgreSQL
POSTGRES_USER=cloudstorage
POSTGRES_PASSWORD=cloudstorage_secret
POSTGRES_DB=cloudstorage

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin_secret

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Google OAuth (получить в Google Cloud Console)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Email (Mailtrap для разработки)
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
```

## 🔧 Технологии

### Backend
- **FastAPI** — веб-фреймворк
- **SQLAlchemy** — ORM
- **PostgreSQL** — база данных
- **MinIO** — объектное хранилище
- **JWT** — аутентификация
- **Pydantic** — валидация данных

### Frontend
- **React 18** — UI библиотека
- **shadcn/ui** — компоненты на Radix UI + Tailwind CSS
- **Tailwind CSS** — утилитарные стили
- **Vite** — сборщик
- **Zustand** — управление состоянием
- **React Router** — роутинг
- **Lucide React** — иконки
- **Axios** — HTTP клиент

### Frontend Design System
- Визуальная основа frontend соответствует подходу **shadcn/ui** из https://ui.shadcn.com
- Для проекта принят стиль **`new-york`** с **`baseColor: neutral`** и semantic CSS variables
- Предпочтительный визуальный язык: нейтральные фоны, читаемые карточные поверхности, заметные но аккуратные границы, спокойные тени и простая типографика без маркетингового перегруза
- Основной UX-принцип: пользователь должен сразу видеть главный рабочий блок, вторичные панели и primary action; интерфейс не должен превращаться в текст на пустом полотне
- Рабочие экраны строятся по card-based иерархии: page shell, section cards, nested cards, modal/dropdown overlays
- Нельзя смешивать в одном интерфейсе несколько визуальных языков: Material-like surfaces, маркетинговые hero-блоки и shadcn patterns должны быть разведены по ролям или исключены
- При добавлении новых экранов и компонентов нужно опираться на существующие shadcn patterns, а не изобретать отдельный дизайн-язык
- Конфигурация стиля фронтенда зафиксирована в `frontend/components.json`

### Frontend Reality Check
- `Files` и `Trash` страницы ходят в реальные backend endpoints
- Preview modal рендерит image/PDF через browser-native preview (authenticated download); text/csv/json/docx/xlsx через preview-service; остальные типы показывают "Preview unavailable"
- Upload widget с очередью (макс. 5 параллельных), per-file progress, отмена, retry
- `Security`, `Billing`, `Verify email`, `Reset password` остаются честными статус-экранами там, где backend flow ещё не готов

### Инфраструктура
- **Docker** — контейнеризация
- **Caddy** — reverse proxy
- **Docker Compose** — оркестрация

## 📝 Полезные команды

```bash
# Просмотр логов всех сервисов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f auth

# Перезапуск сервиса
docker-compose restart auth

# Остановка и удаление контейнеров
docker-compose down

# Остановка с удалением volumes
docker-compose down -v

# Сборка без кэша
docker-compose build --no-cache

# Запуск в фоновом режиме
docker-compose up -d

# Масштабирование сервиса
docker-compose up -d --scale file=3
```

## 📄 Лицензия

MIT

## 👥 Команда

Проект разработан командой из 3 разработчиков.

---

**Документ создан:** 31 марта 2026  
**Версия:** 1.0
