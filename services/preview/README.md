# Preview Service

Микросервис для генерации текстовых превью файлов, которые браузер не умеет отображать нативно (DOCX, XLSX). Изображения и PDF рендерятся браузером напрямую через file-service. PDF preview делается на клиенте через `pdfjs-dist` (первая страница).

---

## Архитектура

```
┌──────────┐     ┌──────────┐     ┌──────────────┐
│ Frontend │────▶│ Gateway  │────▶│ Preview Svc  │
│ (React)  │     │ (Caddy)  │     │  :8000       │
└──────────┘     └──────────┘     └──────┬───────┘
                                         │
                                         │ GET /api/files/{id}/download
                                         │ Authorization: Bearer <jwt>
                                         ▼
                                  ┌──────────────┐
                                  │ File Service  │
                                  │  :8000       │
                                  └──────────────┘
```

**Ключевой принцип:** Preview service **не хранит** файлы и **не имеет** доступа к MinIO. Он проксирует скачивание через file-service,转发 `Authorization` заголовок как есть. Валидация JWT происходит целиком на стороне file-service.

---

## Стек

| Компонент | Технология |
|-----------|-----------|
| Framework | FastAPI 0.109 |
| HTTP client | httpx 0.27 (async) |
| DOCX parsing | python-docx 1.1 |
| XLSX parsing | openpyxl 3.1 |
| Logging | structlog 24.1 |
| Config | pydantic-settings 2.1 |
| Server | uvicorn 0.27 |

---

## Быстрый старт

### Через Docker (в составе стека)

```bash
# Из корня проекта
docker compose up preview -d
```

### Локальная разработка

```bash
cd services/preview

# Установка зависимостей
pip install -r requirements.txt

# Запуск (требуется работающий file-service)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Standalone Docker Compose

```bash
cd services/preview
docker compose up --build
# Доступен на http://localhost:8003
```

---

## Переменные окружения

| Переменная | Обязательна | По умолчанию | Описание |
|-----------|-------------|--------------|----------|
| `FILE_SERVICE_URL` | нет | `http://file:8000` | Внутренний URL file-service |
| `SERVICE_API_KEY` | нет | `""` | API-ключ для service-to-service запросов к file-service (передаётся как `X-API-Key`) |
| `CORS_ORIGINS` | нет | `["http://localhost:8080"]` | Разрешённые origins для CORS |
| `PREVIEW_MAX_SIZE` | нет | `10485760` (10 МБ) | Максимальный размер файла для генерации превью |

---

## API Endpoints

### Health

```
GET /health
```

**Response 200:**
```json
{
  "status": "healthy",
  "service": "preview",
  "file_service": "healthy"
}
```

`status` может быть `"degraded"` если file-service недоступен.

---

### Service Info

```
GET /api/preview/
```

**Response 200:**
```json
{
  "message": "Preview Service is running",
  "version": "1.0.0",
  "generated_previews_enabled": true,
  "supported_text_previews": ["txt", "csv", "json", "docx", "xlsx"],
  "note": "Images and PDFs can still use direct file download preview."
}
```

---

### Generate Preview

```
GET /api/preview/{file_id}
Authorization: Bearer <JWT>
```

Генерирует текстовое превью для поддерживаемых типов файлов.

**Path Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `file_id` | UUID | ID файла в file-service |

**Response 200:**
```json
{
  "kind": "text",
  "content": "First 40000 characters...",
  "truncated": false
}
```

**Поддерживаемые MIME-типы:**

| MIME Type | Метод парсинга |
|-----------|---------------|
| `text/plain` | Raw UTF-8 decode |
| `text/csv` | Raw UTF-8 decode |
| `application/json` | Pretty-print (indent=2) |
| `text/*` (любой) | Raw UTF-8 decode |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Извлечение параграфов + таблиц |
| `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Первая таблица, tab-delimited, макс. 100 строк |

**Ошибки:**

| Статус | Описание |
|--------|----------|
| `400` | Невалидный UUID в `file_id` |
| `401` | Отсутствует `Authorization` заголовок |
| `404` | Файл не найден в file-service |
| `403` | Доступ запрещён в file-service |
| `413` | Файл превышает `preview_max_size` |
| `415` | MIME-тип не поддерживается |
| `502` | file-service недоступен |
| `504` | Timeout при запросе к file-service (30 сек) |

---

### 501 Stubs

Все три endpoint'а требуют `Authorization` заголовок, но возвращают `501 Not Implemented`:

```
GET    /api/preview/{file_id}/thumbnail
POST   /api/preview/{file_id}/generate
DELETE /api/preview/{file_id}
```

---

## Лимиты

| Лимит | Значение |
|-------|----------|
| Макс. размер файла для превью | 10 МБ (`PREVIEW_MAX_SIZE`) |
| Макс. длина текста превью | 40 000 символов |
| Макс. строк XLSX | 100 строк |
| Timeout запроса к file-service | 30 секунд |
| Timeout health check | 5 секунд |

---

## Структура проекта

```
services/preview/
├── Dockerfile              # Python 3.11-slim, non-root user
├── docker-compose.yml      # Standalone dev compose (port 8003)
├── requirements.txt        # Зависимости
├── pytest.ini              # Конфигурация pytest
├── src/
│   ├── __init__.py
│   ├── main.py             # FastAPI приложение, эндпоинты, логика превью
│   └── config.py           # Pydantic Settings
└── tests/
    ├── __init__.py
    ├── conftest.py          # AsyncClient fixture
    └── test_preview.py      # 17 unit-тестов
```

---

## Тесты

```bash
cd services/preview
pip install -r requirements.txt
pip install pytest pytest-asyncio

pytest -v
```

**Покрытие:**
- Health check (healthy + degraded)
- Service info
- Auth required на всех endpoint'ах
- Валидация UUID
- Превью: plain text, CSV, JSON (pretty-print), DOCX, XLSX
- Truncation при превышении 40K символов
- Проброс ошибок 404/403 от file-service
- Unsupported media type (415)
- X-API-Key forwarding

---

## Gateway (Caddy)

В корневом `docker-compose.yml` preview service доступен через Caddy gateway:

| Путь | Назначение |
|------|-----------|
| `/api/preview/*` | API превью |
| `/docs/preview` | Swagger UI |
| `/redoc/preview` | ReDoc |
| `/openapi/preview.json` | OpenAPI schema |
| `/health/preview` | Health check |

---

## Контракты с другими сервисами

### File Service

Preview service обращается к file-service:

```
GET /api/files/{file_id}/download
Authorization: Bearer <jwt>        # Пробрасывается от клиента
X-API-Key: <service_api_key>       # Если настроен
```

- **Timeout:** 30 секунд
- **Ошибки:** проксируются как есть (404, 403, 500)
- **Размер:** ограничивается `preview_max_size` (10 МБ)

### Auth Service

Preview service **не взаимодействует** с auth-service напрямую. JWT валидируется file-service.

---

## Безопасность

- **Non-root Docker user** — контейнер работает от `app:app`
- **SSRF protection** — `file_id` валидируется как UUID перед запросом к file-service
- **No MinIO access** — прямой доступ к хранилищу отсутствует
- **Auth passthrough** — JWT не декодируется, передаётся как есть
- **Size guard** — файлы > 10 МБ отклоняются до полного скачивания
- **Stream reading** — ответ читается чанками (8 КБ) с ранней остановкой при превышении лимита

---

## Логирование

Каждый запрос логируется через `structlog` с `request_id`:

```json
{
  "event": "preview_request",
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

`request_id` генерируется автоматически или подхватывается из заголовка `X-Request-ID`.

---

## Roadmap

- [ ] Thumbnail generation (image resizing)
- [ ] Background preview generation & caching
- [ ] Redis cache для сгенерированных превью
- [ ] PDF → image conversion для thumbnail
- [ ] Multi-sheet XLSX support
