using Cfs.Bff.Infrastructure.Server;
using Cfs.Bff.Options;
using Cfs.Contracts.System;
using Microsoft.Extensions.Options;

namespace Cfs.Bff.Handlers.Get;

public sealed class HealthGetHandler(IOptions<BackendServicesOptions> options) : BffGetHandler
{
    public override string Pattern => "/api/health";

    public override Task<BffHandlerResponse> HandleRequestAsync(HttpContext context, CancellationToken cancellationToken)
    {
        var current = options.Value;

        var response = new ApiHealthResponse(
            "ok",
            DateTimeOffset.UtcNow,
            new Dictionary<string, string>
            {
                ["mode"] = current.Mode.ToString().ToLowerInvariant(),
                ["auth"] = DescribeEndpoint(current.Auth.BaseUrl),
                ["files"] = DescribeEndpoint(current.Files.BaseUrl),
                ["storage"] = DescribeEndpoint(current.Storage.BaseUrl)
            });

        return Task.FromResult(new BffHandlerResponse(Results.Ok(response)));
    }

    public override void Initialize(BffServer? server)
    {
    }

    private static string DescribeEndpoint(string? baseUrl) =>
        string.IsNullOrWhiteSpace(baseUrl)
            ? "not-configured"
            : baseUrl;
}
