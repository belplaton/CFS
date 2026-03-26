namespace Cfs.Contracts.Files;

public sealed record BrowseRootResponse(
    string Path,
    IReadOnlyList<BrowserItemSummary> Items);
