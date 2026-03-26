# Frontend Runbook

This file documents the current frontend service shape after the `update loo` merge was aligned with the active frontend architecture.

## Service Layout

- `frontend/app`: Blazor WebAssembly client
- `frontend/bff`: ASP.NET Core BFF
- `frontend/contracts`: shared DTOs

## BFF Gateway Modes

The BFF no longer uses `UseMockGateways` inside configuration files.

Current source of truth:

```json
{
  "BackendServices": {
    "Mode": "Mock | Remote"
  }
}
```

Supported environment overrides:

- `BACKEND_SERVICES_MODE=Mock|Remote`
- `USE_MOCK_GATEWAYS=true|false`
- `AUTH_SERVICE_URL=http://localhost:8081`
- `FILE_SERVICE_URL=http://localhost:8082`
- `STORAGE_SERVICE_URL=http://localhost:8083`
- `CORS_ALLOWED_ORIGINS=http://localhost:5080,http://localhost:3000`

`USE_MOCK_GATEWAYS` is kept only as a compatibility bridge for older local scripts.

## Active Gateway Implementations

- `frontend/bff/Auth/InMemoryAuthGateway.cs`
- `frontend/bff/Auth/RemoteAuthGateway.cs`
- `frontend/bff/Files/InMemoryWorkspaceGateway.cs`
- `frontend/bff/Files/RemoteWorkspaceGateway.cs`

The older `RealAuthGateway` and `RealWorkspaceGateway` files from `update loo` are obsolete and were removed because they target the pre-refactor gateway contracts.

## Frontend Session Flow

The browser client now:

1. Stores the current session in `localStorage`
2. Restores it during app bootstrap
3. Validates it through `GET /api/auth/me`
4. Clears it on `401`
5. Shows a non-fatal warning when the BFF is temporarily unavailable

Relevant files:

- `frontend/app/App.razor`
- `frontend/app/Services/SessionState.cs`
- `frontend/app/Services/SessionCoordinator.cs`
- `frontend/app/Services/BrowserSessionStore.cs`
- `frontend/app/Services/Api/CfsApiClient.cs`

## Local Start

### BFF only

```bash
cd frontend/bff
dotnet run
```

### Blazor app only

```bash
cd frontend/app
dotnet run
```

### Full frontend solution

```bash
cd frontend
dotnet build CFS.sln
```

## Notes

- `frontend/app/wwwroot/appsettings.json` is the runtime client configuration for `ApiBaseUrl`.
- `frontend/bff/appsettings.Development.json` keeps development mode on `Mock`.
- `frontend/bff/appsettings.json` describes the remote topology.
