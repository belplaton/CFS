using Cfs.Bff.Auth;
using Cfs.Bff.Infrastructure.Http;
using Cfs.Bff.Infrastructure.Server;
using Cfs.Contracts.Auth;
using Cfs.Contracts.Common;

namespace Cfs.Bff.Handlers.Post;

public sealed class LoginPostHandler(IAuthGateway authGateway) : BffPostHandler
{
    public override string Pattern => "/api/auth/login";

    public override async Task<BffHandlerResponse> HandleRequestAsync(HttpContext context, CancellationToken cancellationToken)
    {
        var request = await context.Request.ReadFromJsonAsync<LoginRequest>(cancellationToken);
        if (request is null)
        {
            return new BffHandlerResponse(Results.BadRequest(new ApiError(
                "auth.invalid_request",
                "Request body is required.")));
        }

        if (string.IsNullOrWhiteSpace(request.Email) || string.IsNullOrWhiteSpace(request.Password))
        {
            return new BffHandlerResponse(Results.BadRequest(new ApiError(
                "auth.invalid_credentials",
                "Email and password are required.")));
        }

        try
        {
            var session = await authGateway.LoginAsync(request, cancellationToken);
            return new BffHandlerResponse(Results.Ok(session));
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
