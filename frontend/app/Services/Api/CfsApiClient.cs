using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using Cfs.Contracts.Auth;
using Cfs.Contracts.Common;
using Cfs.Contracts.Files;
using Cfs.Contracts.System;
using Cfs.Frontend.Services;

namespace Cfs.Frontend.Services.Api;

public sealed class CfsApiClient(
    HttpClient httpClient,
    SessionState sessionState,
    SessionCoordinator sessionCoordinator)
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        Converters = { new JsonStringEnumConverter() }
    };

    public async Task<ApiHealthResponse> GetHealthAsync(CancellationToken cancellationToken = default)
    {
        using var response = await httpClient.GetAsync("api/health", cancellationToken);
        await EnsureSuccessAsync(response, cancellationToken);

        return await ReadRequiredAsync<ApiHealthResponse>(
            response,
            "BFF health endpoint returned an empty response.",
            cancellationToken);
    }

    public async Task<AuthSessionResponse> LoginAsync(LoginRequest request, CancellationToken cancellationToken = default)
    {
        using var response = await httpClient.PostAsJsonAsync(
            "api/auth/login",
            request,
            JsonOptions,
            cancellationToken);

        await EnsureSuccessAsync(response, cancellationToken);

        var session = await ReadRequiredAsync<AuthSessionResponse>(
            response,
            "Login response was empty.",
            cancellationToken);

        await sessionCoordinator.SignInAsync(session);
        return session;
    }

    public async Task<UserSummary?> GetCurrentUserAsync(CancellationToken cancellationToken = default)
    {
        using var request = CreateAuthorizedRequest(HttpMethod.Get, "api/auth/me");
        using var response = await httpClient.SendAsync(request, cancellationToken);

        if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
        {
            await sessionCoordinator.SignOutAsync(
                "Saved session expired. Sign in again.",
                SessionNoticeLevel.Info);
            return null;
        }

        await EnsureSuccessAsync(response, cancellationToken);

        return await ReadRequiredAsync<UserSummary>(
            response,
            "Current user response was empty.",
            cancellationToken);
    }

    public async Task<BrowseRootResponse> GetRootAsync(CancellationToken cancellationToken = default)
    {
        using var request = CreateAuthorizedRequest(HttpMethod.Get, "api/files/root");
        using var response = await httpClient.SendAsync(request, cancellationToken);

        if (response.StatusCode == System.Net.HttpStatusCode.Unauthorized)
        {
            await sessionCoordinator.SignOutAsync(
                "Session expired. Sign in again.",
                SessionNoticeLevel.Info);
            throw new ApiClientException(
                "Session expired. Sign in again.",
                System.Net.HttpStatusCode.Unauthorized,
                "auth.unauthorized");
        }

        await EnsureSuccessAsync(response, cancellationToken);

        return await ReadRequiredAsync<BrowseRootResponse>(
            response,
            "Workspace response was empty.",
            cancellationToken);
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
            await sessionCoordinator.SignOutAsync(
                "Session expired. Sign in again.",
                SessionNoticeLevel.Info);
            throw new ApiClientException(
                "Session expired. Sign in again.",
                System.Net.HttpStatusCode.Unauthorized,
                "auth.unauthorized");
        }

        await EnsureSuccessAsync(response, cancellationToken);

        return await ReadRequiredAsync<BrowseRootResponse>(
            response,
            "Create folder response was empty.",
            cancellationToken);
    }

    private HttpRequestMessage CreateAuthorizedRequest(HttpMethod method, string uri)
    {
        if (string.IsNullOrWhiteSpace(sessionState.AccessToken))
        {
            throw new ApiClientException(
                "No active session. Sign in first.",
                System.Net.HttpStatusCode.Unauthorized,
                "auth.unauthorized");
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
        throw new ApiClientException(message, response.StatusCode, error?.Code);
    }

    private static async Task<T> ReadRequiredAsync<T>(
        HttpResponseMessage response,
        string emptyPayloadMessage,
        CancellationToken cancellationToken)
    {
        return await response.Content.ReadFromJsonAsync<T>(JsonOptions, cancellationToken)
               ?? throw new InvalidOperationException(emptyPayloadMessage);
    }
}
