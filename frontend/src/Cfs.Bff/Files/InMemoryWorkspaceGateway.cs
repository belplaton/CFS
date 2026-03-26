using System.Collections.Concurrent;
using Cfs.Contracts.Files;

namespace Cfs.Bff.Files;

internal sealed class InMemoryWorkspaceGateway : IWorkspaceGateway
{
    private readonly ConcurrentDictionary<Guid, List<BrowserItemSummary>> _itemsByUser = new();

    public ValueTask<BrowseRootResponse> GetRootAsync(Guid userId, CancellationToken cancellationToken)
    {
        var items = _itemsByUser.GetOrAdd(userId, static _ => CreateSeedItems());

        lock (items)
        {
            return ValueTask.FromResult(CreateResponse(items));
        }
    }

    public ValueTask<BrowseRootResponse> CreateFolderAsync(Guid userId, CreateFolderRequest request, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Name))
        {
            throw new InvalidOperationException("Folder name is required.");
        }

        var items = _itemsByUser.GetOrAdd(userId, static _ => CreateSeedItems());

        lock (items)
        {
            var normalizedName = request.Name.Trim();
            var alreadyExists = items.Any(item =>
                item.Kind == BrowserItemKind.Folder &&
                string.Equals(item.Name, normalizedName, StringComparison.OrdinalIgnoreCase));

            if (alreadyExists)
            {
                throw new InvalidOperationException("A folder with this name already exists.");
            }

            items.Add(new BrowserItemSummary(
                Guid.NewGuid(),
                normalizedName,
                BrowserItemKind.Folder,
                0,
                DateTimeOffset.UtcNow,
                false));

            return ValueTask.FromResult(CreateResponse(items));
        }
    }

    private static BrowseRootResponse CreateResponse(List<BrowserItemSummary> items)
    {
        var orderedItems = items
            .OrderBy(item => item.Kind)
            .ThenBy(item => item.Name, StringComparer.OrdinalIgnoreCase)
            .ToArray();

        return new BrowseRootResponse("/", orderedItems);
    }

    private static List<BrowserItemSummary> CreateSeedItems()
    {
        var now = DateTimeOffset.UtcNow;

        return
        [
            new BrowserItemSummary(
                Guid.NewGuid(),
                "Design",
                BrowserItemKind.Folder,
                0,
                now.AddMinutes(-34),
                false),
            new BrowserItemSummary(
                Guid.NewGuid(),
                "Network Contracts",
                BrowserItemKind.Folder,
                0,
                now.AddMinutes(-22),
                true),
            new BrowserItemSummary(
                Guid.NewGuid(),
                "roadmap.md",
                BrowserItemKind.File,
                18_432,
                now.AddMinutes(-11),
                false),
            new BrowserItemSummary(
                Guid.NewGuid(),
                "screenshots.zip",
                BrowserItemKind.File,
                2_456_789,
                now.AddMinutes(-6),
                true)
        ];
    }
}
