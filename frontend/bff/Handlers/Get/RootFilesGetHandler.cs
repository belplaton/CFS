using Cfs.Bff.Files;
using Cfs.Bff.Infrastructure;
using Cfs.Bff.Infrastructure.Http;
using Cfs.Bff.Infrastructure.Server;

namespace Cfs.Bff.Handlers.Get;

public sealed class RootFilesGetHandler(
    IWorkspaceGateway workspaceGateway) : BffGetHandler
{
    public override string Pattern => "/api/files/root";

    public override async Task<BffHandlerResponse> HandleRequestAsync(HttpContext context, CancellationToken cancellationToken)
    {
        var accessToken = context.TryGetBearerToken();
        if (string.IsNullOrWhiteSpace(accessToken))
        {
            return new BffHandlerResponse(Results.Unauthorized());
        }

        try
        {
            var response = await workspaceGateway.GetRootAsync(accessToken, cancellationToken);
            return new BffHandlerResponse(Results.Ok(response));
        }
        catch (UpstreamApiException exception)
        {
            return new BffHandlerResponse(exception.ToResult());
        }
    }

    public override void Initialize(BffServer? server)
    {
    }
}
