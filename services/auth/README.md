# Auth Service

Authentication and user management microservice for Cloud File Storage (CFS).

**Stack:** FastAPI 0.109 · PostgreSQL 15 (asyncpg) · Redis 7 · Alembic · structlog · Python 3.11

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [JWT Contract](#jwt-contract)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Database & Migrations](#database--migrations)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Cross-Service Integration](#cross-service-integration)

---

## Overview

The Auth Service is responsible for:

- User registration and authentication (email + password)
- JWT access/refresh token issuance and validation
- Email verification and password reset flows
- Per-user storage quota management (service-to-service endpoint)
- Refresh token revocation (logout)

It is one of three core microservices in the CFS stack, alongside the [File Service](../file/) and [Preview Service](../preview/).

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                     API Layer                         │
│   api/auth.py  ·  api/health.py  ·  api/users.py     │
│   exception_handlers.py                               │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│                   Service Layer                       │
│               services/user_service.py                │
│   (business rules: uniqueness, hashing, tokens)       │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│                 Repository Layer                       │
│       repositories/user.py                            │
│       repositories/verification_token.py              │
│   (all SQL lives here — services never touch SQL)     │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│                   Model Layer                         │
│          models/user.py  ·  models/token.py           │
│   (SQLAlchemy 2.0, DeclarativeBase, UUID PKs)         │
└──────────────────────────────────────────────────────┘
```

**Key design decisions:**

- **Services never raise `HTTPException`** — only `DomainError` subclasses. The API layer maps them to HTTP responses via `exception_handlers.py`.
- **Repositories are stateless** — every method takes an `AsyncSession` parameter so it participates in the caller's transaction.
- **UUID primary keys** — `gen_random_uuid()` via pgcrypto, matching the File and Preview services.
- **Fail-open rate limiter** — if Redis is unavailable, requests proceed with a warning logged.

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

### Run with Docker Compose (recommended)

```bash
# From the project root
docker compose up -d

# Verify
curl http://localhost:8080/health/auth
```

The auth service will be available at:
- **Internal:** `http://auth:8000`
- **Via gateway:** `http://localhost:8080/api/auth`
- **Docs:** `http://localhost:8080/docs/auth`

### Run standalone (development)

```bash
cd services/auth

# Create .env from template
cp ../../.env.example .env
# Edit .env — at minimum set JWT_SECRET, SERVICE_API_KEY, DATABASE_URL

# Install dependencies
pip install -r requirements.txt

# Apply migrations
alembic upgrade head

# Start the server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Configuration

All settings are loaded via environment variables (Pydantic v2 `BaseSettings`).

| Variable | Required | Default | Description |
|---|---|---|---|
| `ENV` | no | `development` | `development` / `production` — production enforces secure secrets |
| `DATABASE_URL` | **yes** | — | `postgresql+asyncpg://user:pass@host:5432/db` |
| `JWT_SECRET` | **yes** | — | Shared HS256 secret for all services |
| `JWT_ALGORITHM` | no | `HS256` | |
| `JWT_ISSUER` | no | `auth-service` | `iss` claim in tokens |
| `JWT_AUDIENCE` | no | `cloud-storage` | `aud` claim in tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `30` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | no | `7` | |
| `SERVICE_API_KEY` | **yes** | — | Shared key for service-to-service calls (`X-API-Key`) |
| `REDIS_URL` | no | `None` | `redis://host:6379/0` — `None` disables rate limiting (fail-open) |
| `CORS_ORIGINS` | no | `http://localhost:8080` | Comma-separated allowed origins |
| `DEFAULT_STORAGE_QUOTA` | no | `5368709120` (5 GB) | Free tier quota in bytes |
| `PREMIUM_STORAGE_QUOTA` | no | `107374182400` (100 GB) | Premium tier quota in bytes |
| `FRONTEND_URL` | no | `http://localhost:8080` | Used to build verification/reset action URLs |
| `SMTP_HOST` | no | `None` | SMTP server for email delivery |
| `SMTP_PORT` | no | `587` | |
| `SMTP_USER` | no | `None` | |
| `SMTP_PASSWORD` | no | `None` | |
| `SMTP_FROM_EMAIL` | no | `noreply@cloudstorage.local` | |

**Production guard:** When `ENV=production`, the service refuses to start if `JWT_SECRET` or `SERVICE_API_KEY` contain known insecure placeholder values.

---

## API Endpoints

### POST `/api/auth/register`

Register a new user. Rate limited: 5 req/min per IP.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "string",
  "full_name": "string | null"
}
```

**Response `201`:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errors:** `409` (email exists), `429` (rate limit)

---

### POST `/api/auth/login`

Authenticate with email and password. Rate limited: 10 req/min per IP.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

**Response `200`:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errors:** `401` (bad credentials), `400` (inactive user), `429` (rate limit)

---

### GET `/api/auth/me`

Get current user profile. Requires `Authorization: Bearer <access_token>`.

**Response `200`:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "string | null",
  "is_active": true,
  "is_verified": false,
  "is_admin": false,
  "storage_quota": 5368709120,
  "used_storage": 0,
  "created_at": "2026-01-01T00:00:00Z",
  "last_login": "2026-06-01T12:00:00Z"
}
```

**Errors:** `401` (no/invalid token)

---

### POST `/api/auth/refresh`

Refresh the token pair. Requires `Authorization: Bearer <refresh_token>`.

**Response `200`:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errors:** `401` (invalid/expired/revoked token), `400` (inactive user)

---

### POST `/api/auth/logout`

Revoke a refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response `200`:**
```json
{
  "message": "Logged out successfully"
}
```

---

### POST `/api/auth/forgot-password`

Request a password reset. Rate limited: 3 req/min per IP. Always returns the same response to prevent email enumeration.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response `200`:**
```json
{
  "message": "If email exists, password reset instructions will be sent",
  "action_url": "http://localhost:8080/reset-password?token=...&email=...",
  "token": "..."
}
```

> `action_url` and `token` are non-null only in development when the user exists.

---

### POST `/api/auth/reset-password`

Reset password using a token from forgot-password. Rate limited: 3 req/min per IP.

**Request:**
```json
{
  "token": "string",
  "new_password": "string"
}
```

**Response `200`:**
```json
{
  "message": "Password updated successfully"
}
```

**Errors:** `401` (invalid/expired token)

---

### POST `/api/auth/verify-email/request`

Generate an email verification token. Requires `Authorization: Bearer <access_token>`.

**Response `200`:**
```json
{
  "message": "Verification instructions generated",
  "action_url": "http://localhost:8080/verify-email?token=...&email=...",
  "token": "..."
}
```

---

### GET `/api/auth/verify-email?token={token}`

Verify email using token from query parameter.

**Response `200`:**
```json
{
  "message": "Email verified successfully",
  "email": "user@example.com",
  "verified": true
}
```

**Errors:** `401` (invalid/expired token)

---

### GET `/api/users/{user_id}/quota`

Get per-user storage quota. **Service-to-service only** — requires `X-API-Key` header.

**Response `200`:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "tier": "free",
  "storage_quota": 5368709120,
  "used_storage": 0
}
```

**Errors:** `401` (bad/missing API key), `404` (user not found)

---

### GET `/health`

Health check with database probe.

**Response `200`:**
```json
{
  "status": "healthy",
  "service": "auth",
  "checks": {
    "database": { "ok": true, "latency_ms": 1.2 }
  }
}
```

**Response `503`** when unhealthy.

---

## JWT Contract

All tokens are HS256-signed with the shared `JWT_SECRET`.

### Access Token

| Claim | Value |
|---|---|
| `sub` | UUID string (user ID) |
| `iss` | `auth-service` |
| `aud` | `cloud-storage` |
| `type` | `access` |
| `exp` | now + 30 min |

### Refresh Token

| Claim | Value |
|---|---|
| `sub` | UUID string (user ID) |
| `iss` | `auth-service` |
| `aud` | `cloud-storage` |
| `type` | `refresh` |
| `exp` | now + 7 days |

### Validation Rules (enforced by all services)

- `iss`, `aud`, `exp`, `sub`, `type` are **required**
- `sub` must parse as `UUID`
- `type == "access"` for data endpoints, `type == "refresh"` for token renewal
- File/Preview services validate `iss=auth-service` and `aud=cloud-storage`

---

## Rate Limiting

Redis-backed fixed-window counter. Fail-open on Redis unavailability.

| Endpoint | Limit | Window | Key |
|---|---|---|---|
| `POST /api/auth/register` | 5 req | 60s | Client IP |
| `POST /api/auth/login` | 10 req | 60s | Client IP |
| `POST /api/auth/forgot-password` | 3 req | 60s | Client IP |
| `POST /api/auth/reset-password` | 3 req | 60s | Client IP |

**429 Response:**
```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded: 5 requests per 60s",
    "details": {
      "retry_after": 30,
      "limit": 5,
      "window": 60
    }
  }
}
```

Headers: `Retry-After: {seconds}`

---

## Error Handling

All errors use a consistent envelope:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable message",
    "details": {}
  }
}
```

| Error Code | HTTP Status | Notes |
|---|---|---|
| `authentication_error` | 401 | + `WWW-Authenticate: Bearer` |
| `user_not_found` | 404 | |
| `user_already_exists` | 409 | |
| `invalid_token` | 401 | + `WWW-Authenticate: Bearer` |
| `service_auth_error` | 401 | X-API-Key failures (no Bearer header) |
| `rate_limit_exceeded` | 429 | + `Retry-After` header |
| `domain_error` | 400 | Catch-all |

**Design rule:** Services raise `DomainError` subclasses. The API layer (`exception_handlers.py`) maps them to HTTP responses. Services never raise `HTTPException` directly.

---

## Database & Migrations

### Schema

Two tables, managed by Alembic:

**`users`**
| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | `gen_random_uuid()` |
| `email` | VARCHAR(255) | unique, indexed |
| `password_hash` | VARCHAR(255) | bcrypt |
| `full_name` | VARCHAR(255) | nullable |
| `avatar_url` | VARCHAR(512) | nullable |
| `is_active` | BOOLEAN | default `true` |
| `is_verified` | BOOLEAN | default `false` |
| `is_admin` | BOOLEAN | default `false` |
| `storage_quota` | BIGINT | default 5 GB |
| `used_storage` | BIGINT | default 0 |
| `totp_secret` | VARCHAR(255) | nullable (2FA, future) |
| `is_2fa_enabled` | BOOLEAN | default `false` |
| `created_at` | TIMESTAMPTZ | server default `now()` |
| `updated_at` | TIMESTAMPTZ | nullable, auto-updated |
| `last_login` | TIMESTAMPTZ | nullable |

**`verification_tokens`**
| Column | Type | Notes |
|---|---|---|
| `id` | UUID (PK) | `gen_random_uuid()` |
| `user_id` | UUID (FK) | `users.id`, CASCADE delete |
| `token` | VARCHAR(255) | unique, indexed |
| `token_type` | VARCHAR(50) | `email_verification` or `password_reset` |
| `is_used` | BOOLEAN | default `false` |
| `created_at` | TIMESTAMPTZ | server default `now()` |
| `expires_at` | TIMESTAMPTZ | |

### Migrations

```bash
# Apply all migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1

# View migration history
alembic history --verbose

# Current revision
alembic current
```

The Docker entrypoint runs `alembic upgrade head` automatically before starting the server.

---

## Testing

Tests require Docker (for testcontainers PostgreSQL) or a running PostgreSQL instance.

### Run tests

```bash
cd services/auth

# With Docker running (testcontainers will spin up PostgreSQL)
pytest -v

# Against an existing PostgreSQL (set DATABASE_URL)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/cloudstorage_auth \
  pytest -v

# Inside Docker container
docker exec cloud-auth python -m pytest tests/ -v
```

### Test coverage

| Test | What it verifies |
|---|---|
| `test_register_success` | Registration returns token pair |
| `test_register_duplicate_email` | Duplicate email → 409 `user_already_exists` |
| `test_login_success` | Login with valid credentials |
| `test_get_me_success` | `/me` returns correct profile |
| `test_refresh_with_valid_refresh_token_returns_token_pair` | Refresh token rotation |
| `test_refresh_with_access_token_returns_401` | Access token rejected on refresh |
| `test_refresh_with_invalid_token_returns_401` | Invalid token rejected |
| `test_verify_email_request_and_consume` | Full email verification flow |
| `test_forgot_password_and_reset_password` | Full password reset flow |
| `test_logout_revokes_refresh_token` | Logout invalidates refresh token |
| `test_rate_limit_breach_returns_clean_429` | Rate limit response format |

### Lint

```bash
ruff check src tests
ruff format src tests
```

---

## Project Structure

```
services/auth/
├── src/
│   ├── main.py                       # FastAPI app, lifespan, CORS, middleware
│   ├── config.py                     # Pydantic v2 Settings (ConfigDict)
│   ├── exceptions.py                 # DomainError hierarchy
│   ├── api/
│   │   ├── __init__.py               # Router assembly
│   │   ├── auth.py                   # /api/auth/* endpoints
│   │   ├── health.py                 # GET /health
│   │   ├── users.py                  # GET /api/users/{id}/quota (X-API-Key)
│   │   └── exception_handlers.py     # DomainError → JSON mapping
│   ├── models/
│   │   ├── __init__.py               # DeclarativeBase, engine, get_db
│   │   ├── user.py                   # User (UUID PK)
│   │   └── token.py                  # VerificationToken
│   ├── schemas/
│   │   └── __init__.py               # Pydantic request/response models
│   ├── services/
│   │   └── user_service.py           # Business logic (no SQL, no HTTPException)
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user.py                   # UserRepository (static methods)
│   │   └── verification_token.py     # VerificationTokenRepository
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── request_id.py             # X-Request-ID + structlog binding
│   │   └── access_log.py             # Per-request access logging
│   └── utils/
│       ├── __init__.py
│       ├── security.py               # JWT encode/decode, password hashing
│       ├── dependencies.py           # get_current_user, get_current_verified_user
│       ├── logging.py                # structlog configuration
│       ├── rate_limiter.py           # Redis fixed-window rate limiter
│       └── redis_client.py           # Async Redis singleton + NullRedis stub
├── migrations/
│   ├── env.py                        # Alembic async environment
│   └── versions/
│       └── 0001_initial.py           # users + verification_tokens + pgcrypto
├── tests/
│   ├── conftest.py                   # Fixtures: DB, client, cleanup
│   └── test_auth.py                  # 11 integration tests
├── alembic.ini
├── Dockerfile
├── requirements.txt
└── .env.example                      # (in project root)
```

---

## Cross-Service Integration

### Shared Configuration

| Variable | Value | Set By | Validated By |
|---|---|---|---|
| `JWT_SECRET` | (shared secret) | env | All services |
| `JWT_ISSUER` | `auth-service` | Auth (sets) | File/Preview (validates) |
| `JWT_AUDIENCE` | `cloud-storage` | Auth (sets) | File/Preview (validates) |
| `SERVICE_API_KEY` | (shared secret) | env | Auth (validates quota calls) |
| `REDIS_URL` | `redis://...` | env | Auth (revocation), File (rate limit) |

### How File Service Uses Auth

1. **JWT validation** — File service decodes every incoming token with the shared `JWT_SECRET`, verifying `iss=auth-service`, `aud=cloud-storage`, `type=access`, and `sub` as UUID.
2. **Quota check** — On upload, File service calls `GET /api/users/{user_id}/quota` with `X-API-Key` header to check storage limits.
3. **Refresh revocation** — On logout, Auth service blacklists the refresh token in Redis. File service doesn't participate in revocation (it only sees access tokens).

### Gateway Routing

The Caddy gateway routes `/api/auth/*` to the auth service:

```
/api/auth, /api/auth/*  →  auth:8000
```

Swagger UI is available outside `/api/*` at `/docs/auth`.

---

## License

Internal project — Cloud File Storage (CFS).
