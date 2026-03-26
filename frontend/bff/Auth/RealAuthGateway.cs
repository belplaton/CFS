using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using Cfs.Contracts.Auth;
using Cfs.Bff.Options;
using Microsoft.Extensions.Options;

namespace Cfs.Bff.Auth;

/// <summary>
/// Реальная реализация IAuthGateway для вызова auth-service (Go)
/// </summary>
internal sealed class RealAuthGateway : IAuthGateway
{
    private readonly HttpClient _httpClient;
    private readonly string _authBaseUrl;

    public RealAuthGateway(IOptions<BackendServicesOptions> options, HttpClient httpClient)
    {
        _httpClient = httpClient;
        _authBaseUrl = options.Value.AuthBaseUrl;
    }

    public async ValueTask<AuthSessionResponse?> LoginAsync(LoginRequest request, CancellationToken cancellationToken)
    {
        try
        {
            var response = await _httpClient.PostAsJsonAsync(
                $"{_authBaseUrl}/api/auth/login",
                request,
                cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                return null;
            }

            return await response.Content.ReadFromJsonAsync<AuthSessionResponse>(cancellationToken);
        }
        catch (HttpRequestException)
        {
            return null;
        }
        catch (TaskCanceledException)
        {
            return null;
        }
    }

    public bool TryGetUser(string? accessToken, out UserSummary? user)
    {
        user = null;

        if (string.IsNullOrWhiteSpace(accessToken))
        {
            return false;
        }

        try
        {
            var request = new HttpRequestMessage(HttpMethod.Get, $"{_authBaseUrl}/api/auth/me");
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);

            var response = _httpClient.Send(request);

            if (!response.IsSuccessStatusCode)
            {
                return false;
            }

            user = response.Content.ReadFromJsonAsync<UserSummary>().GetAwaiter().GetResult();
            return user is not null;
        }
        catch
        {
            return false;
        }
    }
}
