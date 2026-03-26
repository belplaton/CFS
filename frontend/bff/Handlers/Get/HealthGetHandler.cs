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
                ["auth"] = current.AuthBaseUrl,
                ["files"] = current.FileBaseUrl,
                ["storage"] = current.StorageBaseUrl
            });

        return Task.FromResult(new BffHandlerResponse(Results.Ok(response)));
    }

    public override void Initialize(BffServer? server)
    {
    }
}
