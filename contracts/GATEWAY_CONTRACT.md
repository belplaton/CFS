# Gateway Contract (Caddy)

Base URL: `http://localhost:8080`

---

## Route Mapping

### API Routes

| Gateway Path | Backend | Notes |
|---|---|---|
| `/api/auth`, `/api/auth/*` | `auth:8000` | |
| `/api/files`, `/api/files/*` | `file:8000` | |
| `/api/folders`, `/api/folders/*` | `file:8000` | Must be in `@file_api` matcher |
| `/api/trash`, `/api/trash/*` | `file:8000` | Must be in `@file_api` matcher |
| `/api/search`, `/api/search/*` | `file:8000` | Must be in `@file_api` matcher |
| `/api/preview`, `/api/preview/*` | `preview:8000` | |

### Health Routes

| Gateway Path | Rewrite | Backend |
|---|---|---|
| `/health` | `/health` | `file:8000` |
| `/health/auth` | `/health` | `auth:8000` |
| `/health/file` | `/health` | `file:8000` |
| `/health/preview` | `/health` | `preview:8000` |

### Swagger / Docs

| Gateway Path | Backend |
|---|---|
| `/docs/auth` | `auth:8000` |
| `/redoc/auth` | `auth:8000` |
| `/openapi/auth.json` | `auth:8000` |
| `/docs/file` | `file:8000` |
| `/redoc/file` | `file:8000` |
| `/openapi/file.json` | `file:8000` |
| `/docs/preview` | `preview:8000` |
| `/redoc/preview` | `preview:8000` |
| `/openapi/preview.json` | `preview:8000` |

### SPA Fallback

All unmatched paths → `frontend:80`

---

## Security Headers

### Global (all requests)

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: no-referrer
Permissions-Policy: geolocation=(), microphone=(), camera=()
Server: (stripped)
```

### API-specific (`/api/*` only)

```
Content-Security-Policy: default-src 'none'; frame-ancestors 'none'
Cache-Control: no-store
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
```

**Important:** These strict headers are NOT applied to `/docs/*`, `/health/*`, or the SPA.

---

## CORS (API routes only)

```
Access-Control-Allow-Origin: http://localhost:8080
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With, X-API-Key
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 86400
```

---

## Adding a New Service

When adding a new service to the gateway:

1. Add a path matcher: `@new_api path /api/new /api/new/*`
2. Add handler: `handle @new_api { reverse_proxy new:8000 }`
3. Add health: `handle /health/new { rewrite * /health; reverse_proxy new:8000 }`
4. Add docs: `handle /docs/new { reverse_proxy new:8000 }` (etc.)
5. Update `@api` matcher if needed for CORS/CSP headers
