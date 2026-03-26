using System.Collections.Concurrent;
using Cfs.Bff.Infrastructure.Http;
using Cfs.Contracts.Files;

namespace Cfs.Bff.Files;

internal sealed class InMemoryWorkspaceGateway : IWorkspaceGateway
{
    private readonly ConcurrentDictionary<string, List<BrowserItemSummary>> _itemsBySession =
        new(StringComparer.Ordinal);

    public ValueTask<BrowseRootResponse> GetRootAsync(string accessToken, CancellationToken cancellationToken)
    {
        var items = _itemsBySession.GetOrAdd(
            RequireAccessToken(accessToken),
            static _ => CreateSeedItems());

        lock (items)
        {
            return ValueTask.FromResult(CreateResponse(items));
        }
    }

    public ValueTask<BrowseRootResponse> CreateFolderAsync(
        string accessToken,
        CreateFolderRequest request,
        CancellationToken cancellationToken)
    {
        var items = _itemsBySession.GetOrAdd(
            RequireAccessToken(accessToken),
            static _ => CreateSeedItems());

        lock (items)
        {
            var normalizedName = request.Name.Trim();
            var alreadyExists = items.Any(item =>
                item.Kind == BrowserItemKind.Folder &&
                string.Equals(item.Name, normalizedName, StringComparison.OrdinalIgnoreCase));

            if (alreadyExists)
            {
                throw new UpstreamApiException(
                    StatusCodes.Status409Conflict,
                    "folders.already_exists",
                    "A folder with this name already exists.",
                    "files");
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

    private static string RequireAccessToken(string? accessToken)
    {
        if (!string.IsNullOrWhiteSpace(accessToken))
        {
            return accessToken;
        }

        throw new UpstreamApiException(
            StatusCodes.Status401Unauthorized,
            "auth.unauthorized",
            "Bearer token is required.",
            "auth");
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
