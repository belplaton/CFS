# Auth Service

Base URL is configured through `BackendServices:Auth:BaseUrl`.

Default paths are configured in:
- [frontend/bff/appsettings.json](../../frontend/bff/appsettings.json)
- [frontend/bff/Options/BackendServicesOptions.cs](../../frontend/bff/Options/BackendServicesOptions.cs)

## `POST /api/auth/login`

Authenticates a user and returns a bearer token plus the public user profile.

Request DTO:
- [LoginRequest](../../frontend/contracts/Auth/LoginRequest.cs)

Response DTO:
- [AuthSessionResponse](../../frontend/contracts/Auth/AuthSessionResponse.cs)

Successful response:

```json
{
  "accessToken": "9d6f0f4108ea47d4b3e4d3f46f535c2a",
  "expiresAtUtc": "2026-03-27T08:15:00Z",
  "user": {
    "id": "eb4de6d1-4c9a-4ff8-8a68-7d645b1b71d0",
    "email": "user@cfs.local",
    "displayName": "Demo User"
  }
}
```

Request example:

```json
{
  "email": "user@cfs.local",
  "password": "secret123"
}
```

Expected statuses:
- `200 OK`: credentials are valid
- `400 Bad Request`: malformed body or invalid credentials
- `503 Service Unavailable`: auth service dependency failure

Error payload:

```json
{
  "code": "auth.invalid_credentials",
  "message": "Email or password is invalid."
}
```

## `GET /api/auth/me`

Returns the current authenticated user for the provided bearer token.

Headers:
- `Authorization: Bearer <access-token>`

Response DTO:
- [UserSummary](../../frontend/contracts/Auth/UserSummary.cs)

Successful response:

```json
{
  "id": "eb4de6d1-4c9a-4ff8-8a68-7d645b1b71d0",
  "email": "user@cfs.local",
  "displayName": "Demo User"
}
```

Expected statuses:
- `200 OK`: token is valid
- `401 Unauthorized`: token is missing, expired, or invalid
- `503 Service Unavailable`: auth service dependency failure

Error payload:

```json
{
  "code": "auth.unauthorized",
  "message": "Bearer token is invalid."
}
```

## Notes

- BFF treats `accessToken` as an opaque bearer token.
- Auth service owns token validation rules and expiry checks.
- `displayName` is required in the response because the current frontend shows it directly after login.
