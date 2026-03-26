using Cfs.Bff.Auth;
using Cfs.Bff.Infrastructure;
using Cfs.Bff.Infrastructure.Http;
using Cfs.Bff.Infrastructure.Server;

namespace Cfs.Bff.Handlers.Get;

public sealed class CurrentUserGetHandler(IAuthGateway authGateway) : BffGetHandler
{
    public override string Pattern => "/api/auth/me";

    public override async Task<BffHandlerResponse> HandleRequestAsync(HttpContext context, CancellationToken cancellationToken)
    {
        var accessToken = context.TryGetBearerToken();
        if (string.IsNullOrWhiteSpace(accessToken))
        {
            return new BffHandlerResponse(Results.Unauthorized());
        }

        try
        {
            var user = await authGateway.GetCurrentUserAsync(accessToken, cancellationToken);
            return new BffHandlerResponse(user is not null ? Results.Ok(user) : Results.Unauthorized());
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
