using Cfs.Contracts.Files;

namespace Cfs.Bff.Files;

public interface IWorkspaceGateway
{
    ValueTask<BrowseRootResponse> GetRootAsync(string accessToken, CancellationToken cancellationToken);

    ValueTask<BrowseRootResponse> CreateFolderAsync(
        string accessToken,
        CreateFolderRequest request,
        CancellationToken cancellationToken);
}
