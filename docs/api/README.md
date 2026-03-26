# API Contracts

This directory defines the upstream contracts that `frontend/bff` expects from the backend services in `Remote` mode.

Current sources of truth:
- DTOs: [frontend/contracts](../../frontend/contracts)
- BFF gateway registration: [frontend/bff/Program.cs](../../frontend/bff/Program.cs)
- Remote adapters:
  - [frontend/bff/Auth/RemoteAuthGateway.cs](../../frontend/bff/Auth/RemoteAuthGateway.cs)
  - [frontend/bff/Files/RemoteWorkspaceGateway.cs](../../frontend/bff/Files/RemoteWorkspaceGateway.cs)

## Rules

- Transport: HTTP/JSON
- Authentication: `Authorization: Bearer <access-token>`
- JSON property naming: `camelCase`
- Enum serialization: string values exactly matching .NET enum names
- Error shape for non-2xx responses:

```json
{
  "code": "files.already_exists",
  "message": "A folder with this name already exists."
}
```

Shared DTO type: [ApiError](../../frontend/contracts/Common/ApiError.cs)

## Services

- [Auth Service](./auth-service.md)
- [File Service](./file-service.md)

## Current BFF Behavior

- `frontend/bff/appsettings.Development.json` runs in `Mock` mode for local frontend work.
- `frontend/bff/appsettings.json` is configured for `Remote` mode and documents the target URLs.
- BFF forwards bearer tokens to upstream services without rewriting them.

## Next Contracts

The next network slice after `login / me / root / create-folder` is:
- `POST /api/files/upload-init`
- `POST /api/files/upload-complete`
- `GET /api/shares/{token}`
- `POST /api/shares`

These endpoints are not fixed yet and should be added only after the current slice is implemented end-to-end.
