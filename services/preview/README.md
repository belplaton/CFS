# Preview Service

Сервис генерации текстовых превью для файлов Cloud File Storage. Обеспечивает превью форматов, которые браузеры не отображают нативно: TXT, CSV, JSON, DOCX, XLSX.

## Стек

| Компонент | Технология |
|---|---|
| Framework | FastAPI (async) |
| ASGI-сервер | Uvicorn |
| HTTP-клиент | httpx (взаимодействие с file-service) |
| Парсинг документов | python-docx (DOCX), openpyxl (XLSX) |
| Логирование | structlog |
| Валидация | Pydantic v2 + pydantic-settings |

## Структура проекта

```
src/
├── main.py                  # FastAPI приложение, эндпоинты, логика превью
└── config.py                # Конфигурация (pydantic-settings)
```

## Быстрый старт

### Docker Compose (рекомендуется)

```bash
docker-compose up --build
```

Сервис будет доступен на внутреннем порту `8000` (проксируется через gateway на `http://localhost:8080/api/preview`).

### Локальная разработка

```bash
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Переменные окружения

| Переменная | Обязательна | По умолчанию | Описание |
|---|---|---|---|
| `FILE_SERVICE_URL` | Нет | `http://file:8000` | URL file-service |
| `SERVICE_API_KEY` | **Да** | — | API-ключ для межсервисного взаимодействия |
| `PREVIEW_MAX_SIZE` | Нет | `10485760` (10 MB) | Максимальный размер файла для превью |
| `CORS_ORIGINS` | Нет | `["http://localhost:8080"]` | Разрешённые origins для CORS |

## API Эндпоинты

### Превью (`/api/preview`)

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/preview/` | Информация о сервисе |
| `GET` | `/api/preview/{file_id}` | Получение текстового превью файла |
| `GET` | `/api/preview/{file_id}/thumbnail` | Thumbnail (реализация в планах) |
| `POST` | `/api/preview/{file_id}/generate` | Генерация превью (реализация в планах) |
| `DELETE` | `/api/preview/{file_id}` | Удаление превью (реализация в планах) |

### Health

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/health` | Проверка здоровья (включая file-service) |

### Получение превью

```
GET /api/preview/{file_id}
Authorization: Bearer <token>
```

**Ответ:**

```json
{
  "kind": "text",
  "content": "Содержимое файла...",
  "truncated": false
}
```

**Поддерживаемые форматы:**

| MIME-тип | Формат | Описание |
|---|---|---|
| `text/plain` | TXT | Полное содержимое |
| `text/csv` | CSV | Полное содержимое |
| `application/json` | JSON | Форматируется с отступами |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | DOCX | Абзацы + таблицы |
| `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | XLSX | Первый лист, до 100 строк |

Для неподдерживаемых типов возвращается `415 Unsupported Media Type`.

## Безопасность

- **Авторизация** — все эндпоинты превью требуют заголовок `Authorization`
- **Rate limiting** — 30 запросов в минуту на пользователя (фиксированное окно, in-memory)
- **Валидация file_id** — UUID-формат, защита от SSRF через path traversal
- **Размер файла** — лимит 10 MB, потоковое чтение с проверкой
- **XXE-защита** — DOCX валидируется как ZIP-архив перед парсингом
- **Санитизация ошибок** — 5xx ошибки upstream не раскрывают внутренние детали

## Тестирование

```bash
pip install -r requirements.txt pytest pytest-asyncio
pytest
```

Тесты покрывают: health-check, авторизацию, превью каждого формата, rate limiting, обработку ошибок file-service, санитизацию 5xx ответов.
