using System.Net.Http.Json;
using Cfs.Bff.Infrastructure.Http;
using Cfs.Bff.Options;
using Cfs.Contracts.Files;
using Microsoft.Extensions.Options;

namespace Cfs.Bff.Files;

internal sealed class RemoteWorkspaceGateway(
    HttpClient httpClient,
    IOptions<BackendServicesOptions> options) : IWorkspaceGateway
{
    private readonly FileServiceOptions _serviceOptions = options.Value.Files;

    public async ValueTask<BrowseRootResponse> GetRootAsync(string accessToken, CancellationToken cancellationToken)
    {
        try
        {
            using var request = UpstreamHttpClientExtensions.CreateAuthorizedRequest(
                HttpMethod.Get,
                _serviceOptions.RootPath,
                accessToken);
            using var response = await httpClient.SendAsync(request, cancellationToken);

            await response.EnsureSuccessAsync("files", cancellationToken);
            return await response.ReadRequiredJsonAsync<BrowseRootResponse>("files", cancellationToken);
        }
        catch (HttpRequestException exception)
        {
            throw CreateTransportException(exception);
        }
        catch (TaskCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            throw CreateTransportException(exception);
        }
    }

    public async ValueTask<BrowseRootResponse> CreateFolderAsync(
        string accessToken,
        CreateFolderRequest request,
        CancellationToken cancellationToken)
    {
        try
        {
            using var upstreamRequest = UpstreamHttpClientExtensions.CreateAuthorizedRequest(
                HttpMethod.Post,
                _serviceOptions.CreateFolderPath,
                accessToken);
            upstreamRequest.Content = JsonContent.Create(request, options: UpstreamHttpClientExtensions.SerializerOptions);

            using var response = await httpClient.SendAsync(upstreamRequest, cancellationToken);

            await response.EnsureSuccessAsync("files", cancellationToken);
            return await response.ReadRequiredJsonAsync<BrowseRootResponse>("files", cancellationToken);
        }
        catch (HttpRequestException exception)
        {
            throw CreateTransportException(exception);
        }
        catch (TaskCanceledException exception) when (!cancellationToken.IsCancellationRequested)
        {
            throw CreateTransportException(exception);
        }
    }

    private static UpstreamApiException CreateTransportException(Exception exception) =>
        new(
            StatusCodes.Status503ServiceUnavailable,
            "files.unavailable",
            "File service is unavailable.",
            "files",
            exception);
}
