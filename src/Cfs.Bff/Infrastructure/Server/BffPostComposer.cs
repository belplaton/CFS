namespace Cfs.Bff.Infrastructure.Server;

public sealed class BffPostComposer : BffRequestComposer<BffPostComposer, BffPostHandler>
{
    protected override Task<IResult> ComposeAsyncInternal(HttpContext context, CancellationToken cancellationToken) =>
        ExecuteHandlersAsync(context, cancellationToken);

    public override void Initialize(string pattern, BffServer server, WebApplication application)
    {
        application.MapPost(pattern, (Delegate)((HttpContext context) => ComposeAsync(context)));
    }
}
