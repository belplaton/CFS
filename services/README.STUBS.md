# Заглушки сервисов для разработки

Этот каталог содержит stub-реализации сервисов для разработки frontend без полной реализации backend.

## 📦 Stub Services

### Auth Service Stub (Go)
- **Файл:** `cmd/stub/main.go`
- **Dockerfile:** `Dockerfile.stub`
- **Порт:** 8081

**Endpoints:**
- `GET /health` - Health check
- `POST /api/auth/login` - Mock аутентификация
- `GET /api/auth/me` - Получение текущего пользователя

### File Service Stub (Python)
- **Файл:** `stub_main.py`
- **Dockerfile:** `Dockerfile.stub`
- **Порт:** 8082

**Endpoints:**
- `GET /health` - Health check
- `GET /api/files/root` - Получение корневых файлов
- `POST /api/folders` - Создание папки

## 🚀 Запуск

### Вариант 1: Локально (без Docker)

**Auth Service Stub:**
```bash
cd services/auth-service
go run cmd/stub/main.go
```

**File Service Stub:**
```bash
cd services/file-service
pip install fastapi uvicorn pydantic
python stub_main.py
```

### Вариант 2: Docker (отдельно)

**Auth Service Stub:**
```bash
docker build -f services/auth-service/Dockerfile.stub -t cfs-auth-stub services/auth-service
docker run -p 8081:8081 --name cfs-auth-stub cfs-auth-stub
```

**File Service Stub:**
```bash
docker build -f services/file-service/Dockerfile.stub -t cfs-file-stub services/file-service
docker run -p 8082:8082 --name cfs-file-stub cfs-file-stub
```

### Вариант 3: Docker Compose с stub-сервисами

1. Откомментируйте секцию stub-сервисов в `docker-compose.yml`
2. Закомментируйте или удалите оригинальные сервисы `auth-service` и `file-service`
3. Установите `USE_MOCK_GATEWAYS=false` в `.env`
4. Запустите:
```bash
docker-compose up -d
```

## ⚙️ Конфигурация BFF

Для использования stub-сервисов установите в `frontend/bff/appsettings.json`:

```json
{
  "UseMockGateways": false,
  "BackendServices": {
    "AuthBaseUrl": "http://localhost:8081",
    "FileBaseUrl": "http://localhost:8082"
  }
}
```

Или через ENV переменные:
```bash
USE_MOCK_GATEWAYS=false
AUTH_SERVICE_URL=http://localhost:8081
FILE_SERVICE_URL=http://localhost:8082
```

## 🧪 Тестирование

### Auth Service
```bash
# Login
curl -X POST http://localhost:8081/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Get current user (используйте токен из login)
curl http://localhost:8081/api/auth/me \
  -H "Authorization: Bearer <your-token>"
```

### File Service
```bash
# Get root files
curl http://localhost:8082/api/files/root \
  -H "Authorization: Bearer any-token"

# Create folder
curl -X POST http://localhost:8082/api/folders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer any-token" \
  -d '{"name":"New Folder"}'
```

## 📝 Примечания

- Stub-сервисы хранят данные в памяти (не персистентны)
- Auth service принимает любые credentials
- File service создаёт тестовые данные для каждого нового токена
- Используйте для разработки frontend без полной backend инфраструктуры
