namespace Cfs.Bff.Infrastructure;

internal static class BearerTokenHttpContextExtensions
{
    public static string? TryGetBearerToken(this HttpContext context)
    {
        var header = context.Request.Headers.Authorization.ToString();
        const string prefix = "Bearer ";

        return header.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)
            ? header[prefix.Length..].Trim()
            : null;
    }
}
