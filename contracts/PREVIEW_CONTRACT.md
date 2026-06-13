# Preview Service Contract

Base URL: `http://preview:8000` (internal) / `http://localhost:8080/api/preview` (via gateway)

---

## Auth

Preview service **does not decode JWT** itself. It forwards the `Authorization` header to file-service as-is. File-service handles all JWT validation.

---

## Preview Strategy (by file type)

| File Type | Preview Method |
|-----------|---------------|
| Image (png, jpg, gif, webp) | Browser-native via authenticated download |
| PDF | Client-side `pdfjs-dist` (renders first page only) |
| Text (txt, csv, json) | Client-side via file-service `/api/files/{id}/text-preview` |
| DOCX, XLSX | Preview-service text extraction (`GET /api/preview/{file_id}`) |
| Other | "Preview unavailable" message in frontend |

---

## Endpoints

### GET /api/preview/{file_id}

Generate a text preview for supported file types.

**Auth:** `Authorization: Bearer <JWT>` — forwarded to file-service

Path params:

| Param | Type | Description |
|-------|------|-------------|
| `file_id` | string (UUID) | The file to preview |

Response `200`:
```json
{
  "kind": "text",
  "content": "First 40000 characters of file content...",
  "truncated": false
}
```

Supported MIME types:

| MIME Type | Preview Method |
|-----------|---------------|
| `text/plain` | Raw UTF-8 decode |
| `text/csv` | Raw UTF-8 decode |
| `application/json` | Pretty-printed with indent=2 |
| `text/*` (any) | Raw UTF-8 decode |
| DOCX | Paragraph + table text extraction |
| XLSX | First worksheet, tab-delimited (max 100 rows) |

Errors:
- `401` — no/invalid Authorization header
- `404` — file not found in file-service
- `403` — access denied in file-service
- `415` — unsupported MIME type
- `502` — file-service unreachable

---

### GET /api/preview/{file_id}/thumbnail

**Status:** `501 Not Implemented`

```json
{ "detail": "Thumbnails are not enabled yet" }
```

---

### POST /api/preview/{file_id}/generate

**Status:** `501 Not Implemented`

```json
{ "detail": "Background preview generation is not enabled yet" }
```

---

### DELETE /api/preview/{file_id}

**Status:** `501 Not Implemented`

```json
{ "detail": "Stored previews are not enabled yet" }
```

---

### GET /api/preview/

Service info (no auth required).

Response `200`:
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

### GET /health

Response `200`:
```json
{
  "status": "healthy",
  "service": "preview"
}
```

---

## Limits

| Limit | Value |
|-------|-------|
| Max preview text | 40,000 characters |
| XLSX max rows | 100 rows |
| File-service fetch timeout | 30 seconds |

---

## Architecture Notes

- Preview is generated **on-the-fly** by fetching from file-service
- No database usage at runtime (despite postgres-preview being in docker-compose)
- No MinIO access — proxied through file-service
- Auth is passthrough — JWT forwarded to file-service

---

## Environment Variables

| Var | Required | Default | Description |
|-----|----------|---------|-------------|
| `ENV` | no | `development` | |
| `FILE_SERVICE_URL` | no | `http://file:8000` | Internal URL |
| `SERVICE_API_KEY` | yes | — | For file-service |
| `DATABASE_URL` | yes | — | Reserved (not used at runtime) |
| `REDIS_URL` | no | `None` | Reserved |
| `MINIO_ENDPOINT` | yes | — | Reserved |
| `MINIO_ACCESS_KEY` | yes | — | Reserved |
| `MINIO_SECRET_KEY` | yes | — | Reserved |
