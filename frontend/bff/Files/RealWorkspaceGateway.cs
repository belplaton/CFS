using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using Cfs.Contracts.Files;
using Cfs.Bff.Options;
using Microsoft.Extensions.Options;

namespace Cfs.Bff.Files;

/// <summary>
/// Реальная реализация IWorkspaceGateway для вызова file-service (Python)
/// </summary>
internal sealed class RealWorkspaceGateway : IWorkspaceGateway
{
    private readonly HttpClient _httpClient;
    private readonly string _fileBaseUrl;

    public RealWorkspaceGateway(IOptions<BackendServicesOptions> options, HttpClient httpClient)
    {
        _httpClient = httpClient;
        _fileBaseUrl = options.Value.FileBaseUrl;
    }

    public async ValueTask<BrowseRootResponse> GetRootAsync(Guid userId, CancellationToken cancellationToken)
    {
        var response = await _httpClient.GetAsync($"{_fileBaseUrl}/api/files/root", cancellationToken);

        response.EnsureSuccessStatusCode();

        return await response.Content.ReadFromJsonAsync<BrowseRootResponse>(cancellationToken)
            ?? throw new InvalidOperationException("Workspace response was empty.");
    }

    public async ValueTask<BrowseRootResponse> CreateFolderAsync(Guid userId, CreateFolderRequest request, CancellationToken cancellationToken)
    {
        var response = await _httpClient.PostAsJsonAsync(
            $"{_fileBaseUrl}/api/folders",
            request,
            cancellationToken);

        response.EnsureSuccessStatusCode();

        return await response.Content.ReadFromJsonAsync<BrowseRootResponse>(cancellationToken)
            ?? throw new InvalidOperationException("Create folder response was empty.");
    }
}
