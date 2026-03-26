# File Service

Base URL is configured through `BackendServices:Files:BaseUrl`.

Default paths are configured in:
- [frontend/bff/appsettings.json](../../frontend/bff/appsettings.json)
- [frontend/bff/Options/BackendServicesOptions.cs](../../frontend/bff/Options/BackendServicesOptions.cs)

All endpoints below require:
- `Authorization: Bearer <access-token>`

The file service may validate the bearer token itself or trust an auth middleware in front of it. From the BFF point of view, the token is forwarded as-is.

## `GET /api/files/root`

Returns the current user's root directory listing.

Response DTO:
- [BrowseRootResponse](../../frontend/contracts/Files/BrowseRootResponse.cs)
- [BrowserItemSummary](../../frontend/contracts/Files/BrowserItemSummary.cs)
- [BrowserItemKind](../../frontend/contracts/Files/BrowserItemKind.cs)

Successful response:

```json
{
  "path": "/",
  "items": [
    {
      "id": "8b6d60db-c6da-450d-b024-189c174a8f82",
      "name": "Design",
      "kind": "Folder",
      "sizeBytes": 0,
      "updatedAtUtc": "2026-03-27T08:10:00Z",
      "isShared": false
    },
    {
      "id": "ef2d5d3f-fc37-4971-bb58-6b7b0720ee16",
      "name": "roadmap.md",
      "kind": "File",
      "sizeBytes": 18432,
      "updatedAtUtc": "2026-03-27T08:12:00Z",
      "isShared": true
    }
  ]
}
```

Expected statuses:
- `200 OK`: listing returned
- `401 Unauthorized`: token is missing or invalid
- `503 Service Unavailable`: file service dependency failure

## `POST /api/folders`

Creates a folder in the current root directory and returns the refreshed root listing.

Request DTO:
- [CreateFolderRequest](../../frontend/contracts/Files/CreateFolderRequest.cs)

Request example:

```json
{
  "name": "HTTP Adapters"
}
```

Response DTO:
- [BrowseRootResponse](../../frontend/contracts/Files/BrowseRootResponse.cs)

Expected statuses:
- `200 OK`: folder created, response contains updated root listing
- `400 Bad Request`: malformed body or empty folder name
- `401 Unauthorized`: token is missing or invalid
- `409 Conflict`: folder with the same name already exists in the current root
- `503 Service Unavailable`: file service dependency failure

Conflict example:

```json
{
  "code": "folders.already_exists",
  "message": "A folder with this name already exists."
}
```

## Notes

- The current frontend slice works only with the root directory. Nested folders are intentionally out of scope for this first contract.
- `kind` must be serialized as string enum values: `Folder` or `File`.
- `updatedAtUtc` must be returned in UTC ISO-8601 format.
- `sizeBytes` for folders should be `0`.
