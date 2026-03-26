using Cfs.Bff.Files;
using Cfs.Bff.Infrastructure;
using Cfs.Bff.Infrastructure.Http;
using Cfs.Bff.Infrastructure.Server;
using Cfs.Contracts.Common;
using Cfs.Contracts.Files;

namespace Cfs.Bff.Handlers.Post;

public sealed class CreateFolderPostHandler(
    IWorkspaceGateway workspaceGateway) : BffPostHandler
{
    public override string Pattern => "/api/folders";

    public override async Task<BffHandlerResponse> HandleRequestAsync(HttpContext context, CancellationToken cancellationToken)
    {
        var accessToken = context.TryGetBearerToken();
        if (string.IsNullOrWhiteSpace(accessToken))
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

        if (string.IsNullOrWhiteSpace(request.Name))
        {
            return new BffHandlerResponse(Results.BadRequest(new ApiError(
                "folders.invalid_request",
                "Folder name is required.")));
        }

        try
        {
            var response = await workspaceGateway.CreateFolderAsync(accessToken, request, cancellationToken);
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
