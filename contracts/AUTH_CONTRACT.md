# Auth Service Contract

Base URL: `http://auth:8000` (internal) / `http://localhost:8080/api/auth` (via gateway)

---

## JWT Contract (shared secret `JWT_SECRET`)

Algorithm: **HS256**

### Access Token

| Claim | Value |
|-------|-------|
| `sub` | UUID string (`"550e8400-e29b-41d4-a716-446655440000"`) |
| `iss` | `"auth-service"` |
| `aud` | `"cloud-storage"` |
| `type` | `"access"` |
| `exp` | now + 30 min |

### Refresh Token

| Claim | Value |
|-------|-------|
| `sub` | UUID string |
| `iss` | `"auth-service"` |
| `aud` | `"cloud-storage"` |
| `type` | `"refresh"` |
| `exp` | now + 7 days |

### Validation Rules (file/preview services must enforce)

- `iss`, `aud`, `exp`, `sub`, `type` are **required**
- `sub` must parse as `UUID`
- `type == "access"` for data endpoints, `type == "refresh"` for token renewal

---

## Service-to-Service Auth

Header: `X-API-Key: <SERVICE_API_KEY>`
Used by file-service to call `GET /api/users/{user_id}/quota`

---

## Rate Limits

| Endpoint | Limit | Key |
|----------|-------|-----|
| `POST /api/auth/register` | 5 req/min | client IP |
| `POST /api/auth/login` | 10 req/min | client IP |
| `POST /api/auth/forgot-password` | 3 req/min | client IP |
| `POST /api/auth/reset-password` | 3 req/min | client IP |

Rate limit response: `429 Too Many Requests`

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded",
    "details": { "retry_after": 30, "limit": 5, "window": 60 }
  }
}
```

---

## Endpoints

### POST /api/auth/register

**Auth:** None (public)

Request:
```json
{
  "email": "user@example.com",       // required, EmailStr
  "password": "string",              // required, 8-100 chars
  "full_name": "string | null"       // optional
}
```

Response `201`:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

Errors: `409` (email exists), `429` (rate limit)

---

### POST /api/auth/login

**Auth:** None (public)

Request:
```json
{
  "email": "user@example.com",       // required
  "password": "string"               // required
}
```

Response `200`:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

Errors: `401` (bad credentials), `400` (inactive user), `429` (rate limit)

---

### GET /api/auth/me

**Auth:** Bearer JWT (access)

Response `200`:
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
  "last_login": "2026-06-01T12:00:00Z | null"
}
```

Errors: `401` (no/invalid token)

---

### POST /api/auth/refresh

**Auth:** Bearer JWT (refresh) — in Authorization header

Response `200`:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

Errors: `401` (invalid/expired/revoked token), `400` (inactive user)

---

### POST /api/auth/logout

**Auth:** None (refresh token in body)

Request:
```json
{
  "refresh_token": "eyJ..."
}
```

Response `200`:
```json
{
  "message": "Logged out successfully"
}
```

---

### POST /api/auth/forgot-password

**Auth:** None (public, rate-limited)

Request:
```json
{
  "email": "user@example.com"
}
```

Response `200`:
```json
{
  "message": "If email exists, password reset instructions will be sent",
  "action_url": "string | null",   // dev only, non-null if user exists
  "token": "string | null"         // dev only, non-null if user exists
}
```

---

### POST /api/auth/reset-password

**Auth:** None (public, rate-limited)

Request:
```json
{
  "token": "string",               // from forgot-password
  "new_password": "string"         // 8-100 chars
}
```

Response `200`:
```json
{
  "message": "Password updated successfully"
}
```

Errors: `401` (invalid/expired token)

---

### POST /api/auth/verify-email/request

**Auth:** Bearer JWT (access)

Response `200`:
```json
{
  "message": "Verification instructions generated",
  "action_url": "string",
  "token": "string"
}
```

---

### GET /api/auth/verify-email?token={token}

**Auth:** None (token in query)

Response `200`:
```json
{
  "message": "Email verified successfully",
  "email": "user@example.com",
  "verified": true
}
```

Errors: `401` (invalid/expired token)

---

### GET /api/users/{user_id}/quota

**Auth:** X-API-Key only (service-to-service)

Response `200`:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "tier": "free",
  "storage_quota": 5368709120,
  "used_storage": 0
}
```

Errors: `401` (bad/missing API key), `404` (user not found)

---

### GET /health

**Auth:** None

Response `200`:
```json
{
  "status": "healthy",
  "service": "auth",
  "checks": {
    "database": { "ok": true, "latency_ms": 1.2 }
  }
}
```

Response `503` when unhealthy.

---

## Error Response Envelope

All errors:
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
|------------|-------------|-------|
| `authentication_error` | 401 | + `WWW-Authenticate: Bearer` |
| `user_not_found` | 404 | |
| `user_already_exists` | 409 | |
| `invalid_token` | 401 | + `WWW-Authenticate: Bearer` |
| `rate_limit_exceeded` | 429 | + `Retry-After` header |
| `domain_error` | 400 | catch-all |

---

## Environment Variables

| Var | Required | Default | Description |
|-----|----------|---------|-------------|
| `ENV` | no | `development` | `development` / `production` |
| `DATABASE_URL` | yes | — | `postgresql+asyncpg://...` |
| `JWT_SECRET` | yes | — | Shared HS256 secret |
| `JWT_ALGORITHM` | no | `HS256` | |
| `JWT_ISSUER` | no | `auth-service` | `iss` claim |
| `JWT_AUDIENCE` | no | `cloud-storage` | `aud` claim |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `30` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | no | `7` | |
| `REDIS_URL` | no | `None` | `redis://...`; None = rate limiter fail-open |
| `SERVICE_API_KEY` | yes | — | For `/api/users/{id}/quota` |
| `CORS_ORIGINS` | no | `http://localhost:8080` | Comma-separated |
