# Cloud File Storage

Аналог Dropbox/Google Drive на микросервисах.

## Статус (июнь 2026)

### Готово
- Регистрация / авторизация (email + пароль)
- Загрузка / скачивание / удаление файлов
- Управление папками (создание, переименование, перемещение, рекурсивное удаление)
- Корзина (soft delete, restore, permanent delete, TTL cleanup 30 дней)
- Квоты и отображение usage в UI (free / pro / team)
- Поиск по имени файлов через backend
- Конфликт имён при загрузке/создании/переименовании/перемещении (reject|rename)
- Bulk операции (удаление, перемещение до 200 файлов)
- Cursor-based пагинация
- Browser-native preview для image / PDF (pdfjs-dist)
- Text preview для txt/csv/json/docx/xlsx через preview-service
- Upload progress widget с очередью (макс. 5 параллельных)
- Audit log + structured logging (structlog)
- Rate limiting (Redis fixed-window)
- Health check endpoints (DB, MinIO, Redis probes)

## Быстрый старт

### 1. Клонирование

```bash
git clone <repository-url>
cd CloudFileStorage
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
```

Отредактируйте `.env` — обязательные переменные: `JWT_SECRET`, `SERVICE_API_KEY`, `REDIS_PASSWORD`.

### 3. Запуск

```bash
docker compose up -d --build
```

### 4. Smoke-проверка

```bash
python scripts/gateway_smoke.py
```

### 5. Остановка

```bash
docker compose down
```

## Сервисы

| Сервис | Описание | README |
|---|---|---|
| Auth Service | Аутентификация, JWT, управление пользователями | [services/auth/README.md](services/auth/README.md) |
| File Service | CRUD файлов/папок, корзина, квоты, поиск | [services/file/README.md](services/file/README.md) |
| Preview Service | Текстовые превью (TXT, CSV, JSON, DOCX, XLSX) | [services/preview/README.md](services/preview/README.md) |
| Frontend | React SPA (shadcn/ui + Zustand) | [frontend/](frontend/) |
| Gateway | Caddy reverse proxy | [gateway/Caddyfile](gateway/Caddyfile) |

## Структура проекта

```
CloudFileStorage/
├── docker-compose.yml          # Оркестрация всех сервисов
├── .env                        # Переменные окружения
├── .env.example                # Пример переменных
├── ARCHITECTURE.md             # Подробная архитектура
│
├── gateway/                    # Caddy Gateway
│   └── Caddyfile
│
├── services/
│   ├── auth/                   # Auth Service (FastAPI)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── src/
│   ├── file/                   # File Service (FastAPI)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── src/
│   └── preview/                # Preview Service (FastAPI)
│       ├── Dockerfile
│       ├── requirements.txt
│       └── src/
│
├── frontend/                   # React SPA
│   ├── src/
│   ├── Dockerfile
│   └── package.json
│
└── scripts/                    # Утилиты для проверки стека
    ├── gateway_smoke.py        # Полный smoke-тест через gateway
    └── check_trash.py          # Ручная проверка корзины
```

## Технологии

### Backend
| Компонент | Технология |
|---|---|
| Фреймворк | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| БД | PostgreSQL 15 |
| Хранилище | MinIO (S3-совместимое) |
| Кэш | Redis 7 |
| JWT | python-jose (HS256) |
| Валидация | Pydantic v2 |
| Миграции | Alembic |
| Логирование | structlog |

### Frontend
| Компонент | Технология |
|---|---|
| Фреймворк | React 18 + Vite |
| UI | shadcn/ui (Radix UI + Tailwind CSS) |
| State | Zustand |
| Роутинг | React Router v6 |
| HTTP | Axios |

### Инфраструктура
| Компонент | Технология |
|---|---|
| Gateway | Caddy 2 |
| Контейнеры | Docker + Docker Compose |
| Оркестрация | Docker Compose |

## Эндпоинты

### Через Gateway (http://localhost:8080)

| Путь | Сервис |
|---|---|
| `/api/auth/*` | Auth Service |
| `/api/files/*`, `/api/folders/*`, `/api/trash/*`, `/api/search/*` | File Service |
| `/api/preview/*` | Preview Service |
| `/health`, `/health/*` | Соответствующий сервис |
| `/docs/auth`, `/docs/file`, `/docs/preview` | Swagger UI |
| `/*` | Frontend (SPA) |

### Межсервисные

| Сервис | Порт | Описание |
|---|---|---|
| PostgreSQL (auth) | 5433 | БД Auth Service |
| PostgreSQL (file) | 5434 | БД File Service |
| MinIO | 9000, 9001 | Объектное хранилище |
| Redis | 6379 | Кэш / rate limiting |

## Переменные окружения

См. `.env.example` для полного списка. Основные:

| Переменная | Обязательна | Описание |
|---|---|---|
| `JWT_SECRET` | Да | Секрет для подписи JWT |
| `SERVICE_API_KEY` | Да | Ключ для межсервисных вызовов |
| `REDIS_PASSWORD` | Да | Пароль Redis |
| `POSTGRES_PASSWORD` | Да | Пароль PostgreSQL |
| `MINIO_ROOT_USER` | Да | Пользователь MinIO |
| `MINIO_ROOT_PASSWORD` | Да | Пароль MinIO |

## Полезные команды

```bash
# Логи всех сервисов
docker compose logs -f

# Логи конкретного сервиса
docker compose logs -f auth

# Перезапуск сервиса
docker compose restart auth

# Остановка и удаление контейнеров
docker compose down

# Остановка с удалением volumes
docker compose down -v

# Сборка без кэша
docker compose build --no-cache

# Масштабирование file-сервиса
docker compose up -d --scale file=3
```

## Лицензия

MIT
