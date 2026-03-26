# 🚀 Инструкция по запуску CFS Frontend

## ✅ Выполненные исправления

### Критичные проблемы (P0)
- [x] Создан `Dockerfile` для frontend (multi-stage build: Blazor + BFF)
- [x] Создан `appsettings.json` для Blazor app с конфигурацией ApiBaseUrl

### Средние проблемы (P1)
- [x] Исправлен CORS в BFF (порт 3000 для Blazor)
- [x] Добавлено чтение ENV переменных в BFF конфигурацию
- [x] Создан `RealAuthGateway` для вызова auth-service
- [x] Создан `RealWorkspaceGateway` для вызова file-service
- [x] Добавлен флаг переключения mock/real gateway

### Дополнительные улучшения (P2)
- [x] Созданы stub-сервисы (Go + Python) для разработки
- [x] Обновлён `docker-compose.yml`
- [x] Обновлён `nginx.conf` (порт 5180 для BFF)

---

## 📋 Варианты запуска

### Вариант 1: Полный запуск с Docker Compose (рекомендуется)

**Требования:**
- Docker Desktop
- .NET 9.0 SDK (для локальной разработки)

**Запуск:**

1. Создайте `.env` файл:
```bash
cp .env.example .env
```

2. Установите переменные для stub-сервисов (если нет реальных):
```bash
# В .env файле
USE_MOCK_GATEWAYS=false
```

3. Запустите все сервисы:
```bash
docker-compose up -d
```

4. Проверьте статус:
```bash
docker-compose ps
```

5. Откройте браузерер:
- **Frontend:** http://localhost (через nginx)
- **BFF Health:** http://localhost:5180/api/health

---

### Вариант 2: Локальная разработка со stub-сервисами

**Шаг 1: Запуск stub-сервисов**

Auth Service Stub (Go):
```bash
cd services/auth-service
go run cmd/stub/main.go
```

File Service Stub (Python):
```bash
cd services/file-service
pip install fastapi uvicorn pydantic
python stub_main.py
```

**Шаг 2: Запуск BFF**

```bash
cd frontend/bff

# Установите переменные окружения
set USE_MOCK_GATEWAYS=false
set AUTH_SERVICE_URL=http://localhost:8081
set FILE_SERVICE_URL=http://localhost:8082

dotnet run
```

**Шаг 3: Запуск Blazor (опционально для разработки)**

```bash
cd frontend/app
dotnet run
```

Откройте: http://localhost:5180 (BFF с Blazor статикой)

---

### Вариант 3: Только mock-сервисы (без stub)

Для быстрой разработки UI без зависимостей:

1. В `frontend/bff/appsettings.json` установите:
```json
{
  "UseMockGateways": true
}
```

2. Запустите только BFF:
```bash
cd frontend/bff
dotnet run
```

3. Откройте: http://localhost:5180

---

## 🔧 Конфигурация

### Переменные окружения BFF

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `USE_MOCK_GATEWAYS` | Использовать mock вместо реальных сервисов | `true` |
| `AUTH_SERVICE_URL` | URL auth-service | `http://localhost:8081` |
| `FILE_SERVICE_URL` | URL file-service | `http://localhost:8082` |
| `STORAGE_SERVICE_URL` | URL storage-service | `http://localhost:8083` |
| `CORS_ALLOWED_ORIGINS` | Разрешённые CORS origin (через запятую) | - |

### appsettings.json (BFF)

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "BackendServices": {
    "AuthBaseUrl": "http://localhost:8081",
    "FileBaseUrl": "http://localhost:8082",
    "StorageBaseUrl": "http://localhost:8083"
  },
  "Cors": {
    "AllowedOrigins": [
      "http://localhost:3000",
      "http://localhost:5180",
      "http://localhost:7080"
    ]
  },
  "UseMockGateways": true
}
```

---

## 🏗 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      Nginx (порт 80/443)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Frontend Container (порт 5180)                 │
│  ┌─────────────────┐         ┌─────────────────────────┐    │
│  │  Blazor WASM    │────────▶│    BFF (ASP.NET Core)   │    │
│  │  (статика)      │         │  ┌───────────────────┐  │    │
│  │                 │         │  │ Gateway Pattern   │  │    │
│  │                 │         │  │ - Mock            │  │    │
│  │                 │         │  │ - Real (HTTP)     │  │    │
│  └─────────────────┘         │  └───────────────────┘  │    │
│                              └─────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌───────────────────────┐         ┌───────────────────────┐
│   Auth Service        │         │   File Service        │
│   (Go или Stub)       │         │   (Python или Stub)   │
│   порт 8081           │         │   порт 8082           │
└───────────────────────┘         └───────────────────────┘
```

---

## 🧪 Тестирование API

### Health Check
```bash
curl http://localhost:5180/api/health
```

### Login (через BFF)
```bash
curl -X POST http://localhost:5180/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

### Get Current User
```bash
curl http://localhost:5180/api/auth/me \
  -H "Authorization: Bearer <your-token>"
```

### Get Root Files
```bash
curl http://localhost:5180/api/files/root \
  -H "Authorization: Bearer <your-token>"
```

### Create Folder
```bash
curl -X POST http://localhost:5180/api/folders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"name":"New Folder"}'
```

---

## 🐛 Решение проблем

### Ошибка CORS
**Симптом:** Browser console показывает CORS error
**Решение:** Проверьте `Cors:AllowedOrigins` в appsettings.json

### BFF не подключается к сервисам
**Симптом:** 500 Internal Server Error
**Решение:** 
1. Проверьте, что сервисы запущены
2. Проверьте URL в ENV переменных
3. Установите `UseMockGateways: true` для теста

### Docker build ошибка
**Симптом:** Ошибка при сборке frontend образа
**Решение:**
```bash
# Очистите кэш Docker
docker builder prune -a

# Попробуйте собрать заново
docker-compose build --no-cache frontend
```

---

## 📁 Структура frontend

```
frontend/
├── Dockerfile                    # ✅ Multi-stage build
├── app/
│   ├── appsettings.json          # ✅ ApiBaseUrl конфигурация
│   ├── Program.cs
│   ├── Pages/
│   │   ├── Home.razor
│   │   └── Login.razor
│   ├── Services/
│   │   ├── CfsApiClient.cs
│   │   └── SessionState.cs
│   └── Layout/
│       ├── MainLayout.razor
│       └── NavMenu.razor
│
├── bff/
│   ├── Program.cs                # ✅ ENV переменные, флаг mock/real
│   ├── appsettings.json          # ✅ CORS, BackendServices, UseMockGateways
│   ├── Auth/
│   │   ├── IAuthGateway.cs
│   │   ├── InMemoryAuthGateway.cs
│   │   └── RealAuthGateway.cs    # ✅ Новый
│   ├── Files/
│   │   ├── IWorkspaceGateway.cs
│   │   ├── InMemoryWorkspaceGateway.cs
│   │   └── RealWorkspaceGateway.cs  # ✅ Новый
│   └── Handlers/
│       └── ...
│
└── contracts/
    └── ...                       # Общие DTO
```

---

## 📞 Следующие шаги

1. **Реализовать auth-service** (Go) с настоящей аутентификацией
2. **Реализовать file-service** (Python) с базой данных
3. **Добавить загрузку файлов** через storage-service
4. **Реализовать дерево папок** с breadcrumb навигацией
5. **Добавить share links** для общих файлов
