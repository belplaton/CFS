# File Service Contract

Base URL: `http://file:8000` (internal) / `http://localhost:8080/api` (via gateway)

---

## Auth

All endpoints except `GET /health` require:

```
Authorization: Bearer <access_token>
```

JWT validated against shared `JWT_SECRET`:
- `iss == "auth-service"`
- `aud == "cloud-storage"`
- `type == "access"`
- `sub` parses as UUID

---

## Rate Limits

| Policy | Limit | Applied To |
|--------|-------|------------|
| `POLICY_UPLOAD` | 20 req/60s | `POST /api/files/upload` |
| `POLICY_DELETE` | 60 req/60s | `DELETE /api/files/{id}`, `DELETE /api/files/{id}/permanent`, `POST /api/files/bulk-delete` |
| `POLICY_DEFAULT` | 300 req/60s | All other endpoints |

Key: client IP (via `X-Forwarded-For` / `X-Real-IP` / `request.client.host`)

Response `429`:
```json
{
  "error": "rate_limit_exceeded",
  "detail": "Rate limit exceeded",
  "extra": { "retry_after": 30 }
}
```

---

## Files

### GET /api/files/

List files and folders in a directory (cursor-based pagination).

Query params:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `folder_id` | UUID | `null` | Folder to list. `null` = root |
| `limit` | int (1-1000) | `200` | Max items per collection |
| `folders_cursor` | string | `null` | Opaque cursor for folders |
| `files_cursor` | string | `null` | Opaque cursor for files |

Cursor format: base64-urlsafe JSON `{"name": "<string>", "id": "<uuid>"}`

Response `200`:
```json
{
  "folders": [
    {
      "id": "uuid",
      "kind": "folder",
      "name": "My Folder",
      "size": 0,
      "mime_type": null,
      "parent_id": "uuid | null",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z | null"
    }
  ],
  "files": [
    {
      "id": "uuid",
      "kind": "file",
      "name": "report.pdf",
      "size": 12345,
      "mime_type": "application/pdf",
      "parent_id": "uuid | null",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z | null"
    }
  ],
  "next_folders_cursor": "string | null",
  "next_files_cursor": "string | null"
}
```

---

### POST /api/files/upload

Upload a file. Content-Type: `multipart/form-data`

Form fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | UploadFile | yes | Max 100 MB |
| `folder_id` | UUID | no | Target folder |

Query params:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `on_conflict` | `reject\|rename` | `reject` | On name collision |

Response `201`:
```json
{
  "id": "uuid",
  "name": "report.pdf",
  "size": 12345,
  "mime_type": "application/pdf"
}
```

Errors: `409` (conflict, includes `suggested_name`), `413` (too large), `415` (unsupported type)

---

### GET /api/files/quota

Response `200`:
```json
{
  "used": 1234567,
  "total": 5368709120,
  "percent": 0.02
}
```

---

### GET /api/files/{file_id}

Response `200`:
```json
{
  "id": "uuid",
  "name": "report.pdf",
  "size": 12345,
  "mime_type": "application/pdf",
  "folder_id": "uuid | null",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z | null",
  "deleted_at": null
}
```

---

### GET /api/files/{file_id}/text-preview

Returns plain-text content for text-like files.

Response `200`:
```json
{
  "content": "First 40000 chars of the file...",
  "truncated": false
}
```

---

### GET /api/files/{file_id}/download

Returns `StreamingResponse` with:
- `Content-Type`: file's MIME type
- `Content-Disposition`: `attachment; filename*=UTF-8''<url-encoded-name>`
- Body: chunked byte stream

---

### POST /api/files/{file_id}/move

Query params:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `on_conflict` | `reject\|rename` | `reject` | On name collision in target folder |

Request:
```json
{
  "folder_id": "uuid | null"       // null = root
}
```

Response `200`:
```json
{ "status": "moved" }
```

Errors: `409` (conflict, includes `suggested_name`), `404` (not found)

---

### PATCH /api/files/{file_id}/rename

Query params:

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `on_conflict` | `reject\|rename` | `reject` | On name collision in same folder |

Request:
```json
{
  "name": "new-name.pdf"           // 1-255 chars
}
```

Response `200`:
```json
{ "status": "renamed" }
```

Errors: `409` (conflict, includes `suggested_name`), `404` (not found)

---

### DELETE /api/files/{file_id}

Soft-delete (moves to trash).

Response `200`:
```json
{ "status": "moved to trash" }
```

---

### POST /api/files/{file_id}/restore

Response `200`:
```json
{ "status": "restored" }
```

---

### DELETE /api/files/{file_id}/permanent

Response `200`:
```json
{ "status": "deleted permanently" }
```

---

### POST /api/files/bulk-delete

Request:
```json
{
  "ids": ["uuid1", "uuid2"]        // 1-200 items
}
```

Response `200`:
```json
{
  "succeeded": 2,
  "failed": 0,
  "errors": {}
}
```

---

### POST /api/files/bulk-move

Request:
```json
{
  "ids": ["uuid1", "uuid2"],       // 1-200 items
  "folder_id": "uuid | null"
}
```

Response `200`:
```json
{
  "succeeded": 2,
  "failed": 0,
  "errors": {}
}
```

---

## Folders

### POST /api/folders/

Request:
```json
{
  "name": "My Folder",             // 1-255 chars
  "parent_id": "uuid | null"       // null = root
}
```

Response `201`:
```json
{
  "id": "uuid",
  "kind": "folder",
  "name": "My Folder",
  "parent_id": "uuid | null",
  "path": "string | null",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": null
}
```

Errors: `404` (parent not found), `409` (cycle detected), `409` (name conflict with existing file or folder, includes `suggested_name`)

---

### GET /api/folders/

Query params:

| Param | Type | Default |
|-------|------|---------|
| `parent_id` | UUID | `null` |
| `limit` | int | `200` |
| `offset` | int | `0` |

Response `200`: `list[FolderResponse]`

---

### GET /api/folders/{folder_id}

Response `200`: `FolderResponse`

---

### PATCH /api/folders/{folder_id}

Request (partial update):
```json
{
  "name": "new-name",              // optional
  "parent_id": "uuid | null"       // optional
}
```

Response `200`:
```json
{ "status": "updated" }
```

Errors: `409` (cycle), `409` (name conflict, includes `suggested_name`), `404` (not found)

---

### DELETE /api/folders/{folder_id}

Recursive soft-delete (BFS traversal).

Response `200`:
```json
{ "status": "moved to trash" }
```

---

## Trash

### GET /api/trash/

Response `200`:
```json
[
  {
    "id": "uuid",
    "name": "report.pdf",
    "kind": "file",
    "size": 12345,
    "mime_type": "application/pdf",
    "original_parent_id": "uuid | null",
    "deleted_at": "2026-06-01T00:00:00Z"
  }
]
```

---

### POST /api/trash/{item_id}/restore

Response `200`:
```json
{ "status": "restored" }
```

---

### DELETE /api/trash/{item_id}/permanent

Response `200`:
```json
{ "status": "deleted permanently" }
```

---

### POST /api/trash/empty

Response `200`:
```json
{
  "status": "trash emptied",
  "deleted": 42
}
```

---

## Search

### GET /api/search/?q={query}

Query params:

| Param | Type | Constraints |
|-------|------|-------------|
| `q` | string | 1-255 chars |

Response `200`:
```json
{
  "results": [
    {
      "id": "uuid",
      "kind": "file",
      "name": "report.pdf",
      "size": 12345,
      "mime_type": "application/pdf",
      "parent_id": "uuid | null",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": null
    }
  ],
  "total": 1,
  "query": "report"
}
```

---

## Health

### GET /health

Response `200`:
```json
{
  "status": "healthy",
  "service": "file",
  "checks": {
    "database": { "ok": true, "latency_ms": 1.2 },
    "minio": { "ok": true, "latency_ms": 3.4 },
    "redis": { "ok": true, "latency_ms": 0.8 }
  }
}
```

Response `503` when unhealthy.

---

## Error Response Envelope

```json
{
  "error": "error_code",
  "detail": "Human-readable message",
  "extra": {}
}
```

| Error Code | HTTP Status |
|------------|-------------|
| `unauthenticated` | 401 |
| `access_denied` | 403 |
| `file_not_found` | 404 |
| `folder_not_found` | 404 |
| `invalid_filename` | 400 |
| `unsupported_file_type` | 415 |
| `payload_too_large` | 413 |
| `quota_exceeded` | 413 |
| `cycle_detected` | 409 |
| `file_name_conflict` | 409 | includes `suggested_name` in `extra` |
| `rate_limit_exceeded` | 429 | includes `retry_after` in `extra` |
| `internal_error` | 500 |

---

## Object Key Layout (MinIO)

Bucket: `cloudstorage`

```
{user_id}/files/{uuid}{ext}      # active files
{user_id}/trash/{uuid}{ext}      # soft-deleted files
{user_id}/preview/{uuid}{ext}    # generated previews
```

---

## Constants

| Name | Value |
|------|-------|
| `MAX_BULK_ITEMS` | 200 |
| `max_upload_size` | 100 MB |
| `stream_chunk_size` | 1 MB |
| `max_filename_length` | 255 bytes UTF-8 |
| `presigned_url_expires` | 900 seconds (15 min) |
| `trash_retention_days` | 30 |

---

## Environment Variables

| Var | Required | Default | Description |
|-----|----------|---------|-------------|
| `ENV` | no | `development` | `development` / `production` |
| `DATABASE_URL` | yes | — | `postgresql+asyncpg://...` |
| `JWT_SECRET` | yes | — | Shared HS256 secret |
| `JWT_ISSUER` | no | `auth-service` | Must match auth service |
| `JWT_AUDIENCE` | no | `cloud-storage` | Must match auth service |
| `REDIS_URL` | no | `None` | `redis://...` |
| `MINIO_ENDPOINT` | yes | — | e.g. `minio:9000` |
| `MINIO_ACCESS_KEY` | yes | — | |
| `MINIO_SECRET_KEY` | yes | — | |
| `MINIO_BUCKET` | no | `cloudstorage` | |
| `SERVICE_API_KEY` | yes | — | For quota endpoint |
| `AUTH_SERVICE_URL` | no | `http://auth:8000` | Quota fetch URL |
