namespace Cfs.Contracts.System;

public sealed record ApiHealthResponse(
    string Status,
    DateTimeOffset GeneratedAtUtc,
    IReadOnlyDictionary<string, string> Upstreams);
