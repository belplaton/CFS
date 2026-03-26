# CFS (Cloud File Storage)

Микросервисное облачное файловое хранилище с возможностью управления файлами и папками.

## 📋 Описание

CFS — это распределённая система для хранения файлов, состоящая из нескольких независимых сервисов:

- **Auth Service** — сервис аутентификации и авторизации (Go + chi)
- **File Service** — сервис управления файлами и папками (Python + FastAPI)
- **Storage Service** — сервис низкоуровневого хранения данных (Go + chi)
- **Frontend** — веб-интерфейс (Blazor)

## 🏗 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      Nginx (Reverse Proxy)                  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Auth Service │   │  File Service │   │   Frontend    │
│    Go + chi   │   │ Python+FastAPI│   │    Blazor     │
└───────────────┘   └───────────────┘   └───────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage Service                          │
│                       Go + chi                              │
│                                                             │
│  ┌─────────────┐         ┌─────────────┐                    │
│  │  PostgreSQL │         │    MinIO    │                    │
│  └─────────────┘         └─────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## 🛠 Технологический стек

### Backend
- **Go 1.26 + chi/v5**
  - Auth Service — аутентификация и авторизация
  - Storage Service — работа с объектным хранилищем MinIO
  - sqlx — работа с PostgreSQL
  
- **Python + FastAPI**
  - File Service — бизнес-логика управления файлами
  - SQLAlchemy + Alembic — ORM и миграции
  - Pydantic — валидация данных
  - python-jose — JWT-токены

### Frontend
- **Blazor** — интерактивный веб-интерфейс
- .NET 6/7/8

### Инфраструктура
- **Docker & Docker Compose** — контейнеризация
- **Nginx** — обратный прокси и балансировка
- **PostgreSQL** — реляционная база данных
- **MinIO** — объектное хранилище

## 🚀 Быстрый старт

### Требования
- Docker и Docker Compose
- Git

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/belplaton/CFS.git
cd CFS
```

2. Создайте файл окружения:
```bash
cp .env.example .env
```

3. Отредактируйте `.env` при необходимости

4. Запустите все сервисы:
```bash
docker-compose up -d
```

5. Проверьте статус контейнеров:
```bash
docker-compose ps
```

6. Откройте браузер и перейдите по адресу `http://localhost`

## 📁 Структура проекта

```
CFS/
├── services/
│   ├── auth-service/         # Сервис аутентификации (Go + chi)
│   │   ├── cmd/
│   │   ├── internal/
│   │   └── pkg/
│   ├── file-service/         # Сервис управления файлами (Python + FastAPI)
│   │   ├── src/
│   │   │   ├── core/
│   │   │   ├── files/
│   │   │   ├── folders/
│   │   │   └── shared/
│   │   ├── tests/
│   │   └── alembic/
│   └── storage-service/      # Сервис хранения (Go + chi)
│       ├── cmd/
│       ├── internal/
│       └── pkg/
├── frontend/                 # Blazor-приложение
├── nginx/
│   └── nginx.conf            # Конфигурация прокси
├── scripts/                  # Скрипты для развёртывания
├── docs/
│   ├── architecture.md
│   ├── api/
│   └── diagrams/
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔧 Разработка

### Запуск отдельных сервисов

```bash
# Auth Service
docker-compose up auth-service

# File Service
docker-compose up file-service

# Storage Service
docker-compose up storage-service
```

### Локальная разработка (без Docker)

#### Auth Service
```bash
cd services/auth-service
go run cmd/app/main.go
```

#### File Service
```bash
cd services/file-service
pip install -r requirements.txt
uvicorn src.main:app --reload
```

#### Storage Service
```bash
cd services/storage-service
go run cmd/app/main.go
```

#### Frontend (Blazor)
```bash
cd frontend
dotnet run
```

### Тесты

```bash
# File Service tests
cd services/file-service
pytest tests/
```

## 📖 Документация

- [Архитектура](docs/architecture.md)
- [API Documentation](docs/api/)
- [Диаграммы](docs/diagrams/)

## 🔐 Безопасность

- Хеширование паролей (bcrypt)
- JWT-токены для аутентификации
- Изолированные микросервисы

## 📝 Лицензия

MIT

## 👥 Авторы

Ангелов Владимир
Беляков Платон
Прибытков Степан
