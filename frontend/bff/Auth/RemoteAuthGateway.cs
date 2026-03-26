using System.Net;
using System.Net.Http.Json;
using Cfs.Bff.Infrastructure.Http;
using Cfs.Bff.Options;
using Cfs.Contracts.Auth;
using Microsoft.Extensions.Options;

namespace Cfs.Bff.Auth;

internal sealed class RemoteAuthGateway(
    HttpClient httpClient,
    IOptions<BackendServicesOptions> options) : IAuthGateway
{
    private readonly AuthServiceOptions _serviceOptions = options.Value.Auth;

    public async ValueTask<AuthSessionResponse> LoginAsync(LoginRequest request, CancellationToken cancellationToken)
    {
        try
        {
            using var response = await httpClient.PostAsJsonAsync(
                _serviceOptions.LoginPath,
                request,
                UpstreamHttpClientExtensions.SerializerOptions,
                cancellationToken);

            await response.EnsureSuccessAsync("auth", cancellationToken);
            return await response.ReadRequiredJsonAsync<AuthSessionResponse>("auth", cancellationToken);
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

    public async ValueTask<UserSummary?> GetCurrentUserAsync(string? accessToken, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(accessToken))
        {
            return null;
        }

        try
        {
            using var request = UpstreamHttpClientExtensions.CreateAuthorizedRequest(
                HttpMethod.Get,
                _serviceOptions.CurrentUserPath,
                accessToken);
            using var response = await httpClient.SendAsync(request, cancellationToken);

            if (response.StatusCode == HttpStatusCode.Unauthorized)
            {
                return null;
            }

            await response.EnsureSuccessAsync("auth", cancellationToken);
            return await response.ReadRequiredJsonAsync<UserSummary>("auth", cancellationToken);
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
            "auth.unavailable",
            "Auth service is unavailable.",
            "auth",
            exception);
}
