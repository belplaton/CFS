namespace Cfs.Bff.Infrastructure.Server;

public sealed class BffGetComposer : BffRequestComposer<BffGetComposer, BffGetHandler>
{
    protected override Task<IResult> ComposeAsyncInternal(HttpContext context, CancellationToken cancellationToken) =>
        ExecuteHandlersAsync(context, cancellationToken);

    public override void Initialize(string pattern, BffServer server, WebApplication application)
    {
        application.MapGet(pattern, (Delegate)((HttpContext context) => ComposeAsync(context)));
    }
}
