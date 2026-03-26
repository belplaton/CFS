using Cfs.Contracts.Files;

namespace Cfs.Bff.Files;

public interface IWorkspaceGateway
{
    ValueTask<BrowseRootResponse> GetRootAsync(Guid userId, CancellationToken cancellationToken);

    ValueTask<BrowseRootResponse> CreateFolderAsync(Guid userId, CreateFolderRequest request, CancellationToken cancellationToken);
}
