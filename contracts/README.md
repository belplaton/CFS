# Service Contracts

Контракты API для независимой разработки сервисов. Каждый сервис можно разрабатывать, тестировать и деплоить отдельно, при условии что контракты соблюдаются.

## Файлы

| Файл | Описание |
|------|----------|
| [AUTH_CONTRACT.md](AUTH_CONTRACT.md) | Auth Service — регистрация, логин, JWT, токены, quota endpoint |
| [FILE_CONTRACT.md](FILE_CONTRACT.md) | File Service — файлы, папки, корзина, поиск, загрузка, скачивание |
| [PREVIEW_CONTRACT.md](PREVIEW_CONTRACT.md) | Preview Service — генерация текстовых превью |
| [GATEWAY_CONTRACT.md](GATEWAY_CONTRACT.md) | Gateway (Caddy) — маршрутизация, security headers, CORS |

## Cross-Service Dependencies

```
┌─────────────┐     JWT (access)      ┌─────────────┐
│   Frontend   │ ──────────────────> │    Auth      │
│   (React)    │ <──────────────────  │   Service    │
└──────┬──────┘     token pair        └──────┬──────┘
       │                                      │
       │ JWT (access)                         │ X-API-Key
       │                                      │ (quota)
       ▼                                      ▼
┌─────────────┐     JWT forwarded    ┌─────────────┐
│    File      │ <────────────────── │   Preview    │
│   Service    │ ──────────────────> │   Service    │
└──────┬──────┘     file bytes       └──────────────┘
       │
       │ MinIO SDK
       ▼
┌─────────────┐
│    MinIO     │
└─────────────┘
```

## Shared Configuration

| Variable | Value | Used By |
|----------|-------|---------|
| `JWT_SECRET` | (shared secret) | auth, file, preview |
| `JWT_ISSUER` | `auth-service` | auth (sets), file/preview (validates) |
| `JWT_AUDIENCE` | `cloud-storage` | auth (sets), file/preview (validates) |
| `SERVICE_API_KEY` | (shared secret) | auth (validates), file (sends) |
| `REDIS_URL` | `redis://...` | auth (revocation), file (rate limit, idempotency) |

## Breaking Change Checklist

При изменении контракта:

- [ ] Обновить relevant `*_CONTRACT.md`
- [ ] Уведомить команды зависимых сервисов
- [ ] Добавить миграцию если меняется JWT формат
- [ ] Проверить backward compatibility (old clients vs new API)
- [ ] Обновить `PASS_1_CONTRACT_MATRIX.txt`
