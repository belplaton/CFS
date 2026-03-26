using Cfs.Bff.Auth;
using Cfs.Bff.Files;
using Cfs.Bff.Infrastructure;
using Cfs.Bff.Infrastructure.Server;
using Cfs.Contracts.Common;
using Cfs.Contracts.Files;

namespace Cfs.Bff.Handlers.Post;

public sealed class CreateFolderPostHandler(
    IAuthGateway authGateway,
    IWorkspaceGateway workspaceGateway) : BffPostHandler
{
    public override string Pattern => "/api/folders";

    public override async Task<BffHandlerResponse> HandleRequestAsync(HttpContext context, CancellationToken cancellationToken)
    {
        if (!authGateway.TryGetUser(context.TryGetBearerToken(), out var user) || user is null)
        {
            return new BffHandlerResponse(Results.Unauthorized());
        }

        var request = await context.Request.ReadFromJsonAsync<CreateFolderRequest>(cancellationToken);
        if (request is null)
        {
            return new BffHandlerResponse(Results.BadRequest(new ApiError(
                "folders.invalid_request",
                "Request body is required.")));
        }

        try
        {
            var response = await workspaceGateway.CreateFolderAsync(user.Id, request, cancellationToken);
            return new BffHandlerResponse(Results.Ok(response));
        }
        catch (InvalidOperationException exception)
        {
            return new BffHandlerResponse(Results.BadRequest(
                new ApiError("folders.invalid_request", exception.Message)));
        }
    }

    public override void Initialize(BffServer? server)
    {
    }
}
