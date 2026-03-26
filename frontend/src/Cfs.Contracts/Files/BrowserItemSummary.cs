namespace Cfs.Contracts.Files;

public sealed record BrowserItemSummary(
    Guid Id,
    string Name,
    BrowserItemKind Kind,
    long SizeBytes,
    DateTimeOffset UpdatedAtUtc,
    bool IsShared);
