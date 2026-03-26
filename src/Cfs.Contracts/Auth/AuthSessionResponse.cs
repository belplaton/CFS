namespace Cfs.Contracts.Auth;

public sealed record AuthSessionResponse(
    string AccessToken,
    DateTimeOffset ExpiresAtUtc,
    UserSummary User);
