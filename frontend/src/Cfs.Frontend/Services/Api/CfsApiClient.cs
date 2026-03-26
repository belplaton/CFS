using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using Cfs.Contracts.Auth;
using Cfs.Contracts.Common;
using Cfs.Contracts.Files;
using Cfs.Contracts.System;

namespace Cfs.Frontend.Services.Api;

public sealed class CfsApiClient(HttpClient httpClient, SessionState sessionState)
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        Converters = { new JsonStringEnumConverter() }
    };

    public async Task<ApiHealthResponse> GetHealthAsync(CancellationToken cancellationToken = default)
    {
        return await httpClient.GetFromJsonAsync<ApiHealthResponse>(
                   "api/health",
                   JsonOptions,
                   cancellationToken)
               ?? throw new InvalidOperationException("BFF health endpoint returned an empty response.");
    }

    public async Task<AuthSessionResponse> LoginAsync(LoginRequest request, CancellationToken cancellationToken = default)
    {
        using var response = await httpClient.PostAsJsonAsync(
            "api/auth/login",
            request,
            JsonOptions,
            cancellationToken);

        await EnsureSuccessAsync(response, cancellationToken);

        var session = await response.Content.ReadFromJsonAsync<AuthSessionResponse>(
                          JsonOptions,
                          cancellationToken)
                      ?? throw new InvalidOperationException("Login response was empty.");

        sessionState.SetSession(session);
        return session;
    }

    public async Task<UserSummary?> GetCurrentUserAsync(CancellationToken cancellationToken = default)
    {
        using var request = CreateAuthorizedRequest(HttpMethod.Get, "api/auth/me");
        using var response = await httpClient.SendAsync(request, cancellationToken);

        if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
        {
            sessionState.Clear();
            return null;
        }

        await EnsureSuccessAsync(response, cancellationToken);

        return await response.Content.ReadFromJsonAsync<UserSummary>(
            JsonOptions,
            cancellationToken);
    }

    public async Task<BrowseRootResponse> GetRootAsync(CancellationToken cancellationToken = default)
    {
        using var request = CreateAuthorizedRequest(HttpMethod.Get, "api/files/root");
        using var response = await httpClient.SendAsync(request, cancellationToken);

        if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
        {
            sessionState.Clear();
            throw new InvalidOperationException("Session expired. Sign in again.");
        }

        await EnsureSuccessAsync(response, cancellationToken);

        return await response.Content.ReadFromJsonAsync<BrowseRootResponse>(
                   JsonOptions,
                   cancellationToken)
               ?? throw new InvalidOperationException("Workspace response was empty.");
    }

    public async Task<BrowseRootResponse> CreateFolderAsync(
        CreateFolderRequest requestBody,
        CancellationToken cancellationToken = default)
    {
        using var request = CreateAuthorizedRequest(HttpMethod.Post, "api/folders");
        request.Content = JsonContent.Create(requestBody, options: JsonOptions);

        using var response = await httpClient.SendAsync(request, cancellationToken);

        if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
        {
            sessionState.Clear();
            throw new InvalidOperationException("Session expired. Sign in again.");
        }

        await EnsureSuccessAsync(response, cancellationToken);

        return await response.Content.ReadFromJsonAsync<BrowseRootResponse>(
                   JsonOptions,
                   cancellationToken)
               ?? throw new InvalidOperationException("Create folder response was empty.");
    }

    private HttpRequestMessage CreateAuthorizedRequest(HttpMethod method, string uri)
    {
        if (string.IsNullOrWhiteSpace(sessionState.AccessToken))
        {
            throw new InvalidOperationException("No active session. Sign in first.");
        }

        var request = new HttpRequestMessage(method, uri);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", sessionState.AccessToken);
        return request;
    }

    private static async Task EnsureSuccessAsync(HttpResponseMessage response, CancellationToken cancellationToken)
    {
        if (response.IsSuccessStatusCode)
        {
            return;
        }

        var error = await response.Content.ReadFromJsonAsync<ApiError>(JsonOptions, cancellationToken);
        var message = error?.Message ?? $"Request failed with status code {(int)response.StatusCode}.";
        throw new InvalidOperationException(message);
    }
}
