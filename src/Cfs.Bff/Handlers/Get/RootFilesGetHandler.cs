using Cfs.Bff.Auth;
using Cfs.Bff.Files;
using Cfs.Bff.Infrastructure;
using Cfs.Bff.Infrastructure.Server;

namespace Cfs.Bff.Handlers.Get;

public sealed class RootFilesGetHandler(
    IAuthGateway authGateway,
    IWorkspaceGateway workspaceGateway) : BffGetHandler
{
    public override string Pattern => "/api/files/root";

    public override async Task<BffHandlerResponse> HandleRequestAsync(HttpContext context, CancellationToken cancellationToken)
    {
        if (!authGateway.TryGetUser(context.TryGetBearerToken(), out var user) || user is null)
        {
            return new BffHandlerResponse(Results.Unauthorized());
        }

        var response = await workspaceGateway.GetRootAsync(user.Id, cancellationToken);
        return new BffHandlerResponse(Results.Ok(response));
    }

    public override void Initialize(BffServer? server)
    {
    }
}
