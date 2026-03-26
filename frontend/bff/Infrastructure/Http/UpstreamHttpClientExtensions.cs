using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using Cfs.Contracts.Common;

namespace Cfs.Bff.Infrastructure.Http;

internal static class UpstreamHttpClientExtensions
{
    public static JsonSerializerOptions SerializerOptions { get; } = new(JsonSerializerDefaults.Web)
    {
        Converters = { new JsonStringEnumConverter() }
    };

    public static HttpRequestMessage CreateAuthorizedRequest(HttpMethod method, string requestUri, string accessToken)
    {
        var request = new HttpRequestMessage(method, requestUri);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", accessToken);
        return request;
    }

    public static async Task EnsureSuccessAsync(
        this HttpResponseMessage response,
        string serviceName,
        CancellationToken cancellationToken)
    {
        if (response.IsSuccessStatusCode)
        {
            return;
        }

        ApiError? error = null;

        try
        {
            error = await response.Content.ReadFromJsonAsync<ApiError>(SerializerOptions, cancellationToken);
        }
        catch (JsonException)
        {
        }
        catch (NotSupportedException)
        {
        }

        var statusCode = (int)response.StatusCode;

        throw new UpstreamApiException(
            statusCode,
            error?.Code ?? $"{serviceName}.request_failed",
            error?.Message ?? $"{serviceName} service request failed with status code {statusCode}.",
            serviceName);
    }

    public static async Task<T> ReadRequiredJsonAsync<T>(
        this HttpResponseMessage response,
        string serviceName,
        CancellationToken cancellationToken)
    {
        var payload = await response.Content.ReadFromJsonAsync<T>(SerializerOptions, cancellationToken);
        if (payload is not null)
        {
            return payload;
        }

        throw new UpstreamApiException(
            StatusCodes.Status502BadGateway,
            $"{serviceName}.empty_response",
            $"{serviceName} service returned an empty response.",
            serviceName);
    }
}
