using System.Text.Json;
using System.Text.Json.Serialization;
using Cfs.Contracts.Auth;
using Microsoft.JSInterop;

namespace Cfs.Frontend.Services;

public sealed class BrowserSessionStore(IJSRuntime jsRuntime)
{
    private const string StorageKey = "cfs.session";

    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web)
    {
        Converters = { new JsonStringEnumConverter() }
    };

    public async ValueTask<AuthSessionResponse?> GetAsync()
    {
        var raw = await jsRuntime.InvokeAsync<string?>("localStorage.getItem", StorageKey);
        if (string.IsNullOrWhiteSpace(raw))
        {
            return null;
        }

        try
        {
            return JsonSerializer.Deserialize<AuthSessionResponse>(raw, JsonOptions);
        }
        catch (JsonException)
        {
            await ClearAsync();
            return null;
        }
    }

    public ValueTask SaveAsync(AuthSessionResponse session)
    {
        var payload = JsonSerializer.Serialize(session, JsonOptions);
        return jsRuntime.InvokeVoidAsync("localStorage.setItem", StorageKey, payload);
    }

    public ValueTask ClearAsync() =>
        jsRuntime.InvokeVoidAsync("localStorage.removeItem", StorageKey);
}
