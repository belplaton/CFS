# ☁️ Cloud File Storage

Аналог Dropbox/Google Drive на микросервисах

## 📋 Описание

Проект представляет собой облачное хранилище файлов с микросервисной архитектурой.

### Основные возможности (MVP)
- ✅ Регистрация / авторизация (email + пароль)
- ✅ Вход через Google (OAuth2)
- ✅ Двухфакторная аутентификация (TOTP)
- ✅ Верификация email
- ✅ Восстановление пароля
- ✅ Загрузка / скачивание / удаление файлов
- ✅ Управление папками
- ✅ Предпросмотр файлов
- ✅ Поиск по имени файла
- ✅ Корзина (30 дней)
- ✅ Квоты: 5 ГБ (бесплатно), 100 ГБ (подписка)

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
# Ручная сборка frontend
docker-compose build frontend
docker create --name temp-frontend cloudfilestorage-frontend
docker cp temp-frontend:/frontend/dist/. ./frontend/dist/
docker rm temp-frontend

# Запуск сервисов
docker-compose up -d
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

### 5. Проверка работы

| Сервис | URL | Описание |
|--------|-----|----------|
| **Frontend** | http://localhost:8080 | Веб-интерфейс |
| **Auth Service** | http://localhost:8080/api/auth/ | API аутентификации |
| **File Service** | http://localhost:8080/api/files/ | API файлов |
| **Preview Service** | http://localhost:8080/api/preview/ | API превью |
| **Health Check** | http://localhost:8080/health | Проверка статуса |
| **Auth DB** | localhost:5433 | PostgreSQL (Auth Service) |
| **File DB** | localhost:5434 | PostgreSQL (File Service) |
| **Preview DB** | localhost:5435 | PostgreSQL (Preview Service) |
| **MinIO Console** | http://localhost:9001 | Консоль MinIO (только локально) |
| **Redis** | localhost:6379 | Redis |

### 6. API Документация

Каждый сервис предоставляет Swagger UI:

- Auth Service: http://localhost:8080/api/auth/docs
- File Service: http://localhost:8080/api/files/docs
- Preview Service: http://localhost:8080/api/preview/docs

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
