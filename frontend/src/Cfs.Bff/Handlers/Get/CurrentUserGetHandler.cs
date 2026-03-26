using Cfs.Bff.Auth;
using Cfs.Bff.Infrastructure;
using Cfs.Bff.Infrastructure.Server;

namespace Cfs.Bff.Handlers.Get;

public sealed class CurrentUserGetHandler(IAuthGateway authGateway) : BffGetHandler
{
    public override string Pattern => "/api/auth/me";

    public override Task<BffHandlerResponse> HandleRequestAsync(HttpContext context, CancellationToken cancellationToken)
    {
        var result = authGateway.TryGetUser(context.TryGetBearerToken(), out var user) && user is not null
            ? Results.Ok(user)
            : Results.Unauthorized();

        return Task.FromResult(new BffHandlerResponse(result));
    }

    public override void Initialize(BffServer? server)
    {
    }
}
