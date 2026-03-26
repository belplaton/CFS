namespace Cfs.Bff.Infrastructure.Server;

public abstract class BffRequestHandler<TBffRequestComposer, TBffRequestHandler> :
    IBffRequestHandler<TBffRequestComposer, TBffRequestHandler>
    where TBffRequestComposer : BffRequestComposer<TBffRequestComposer, TBffRequestHandler>, new()
    where TBffRequestHandler : BffRequestHandler<TBffRequestComposer, TBffRequestHandler>
{
    public abstract string Pattern { get; }

    public abstract Task<BffHandlerResponse> HandleRequestAsync(HttpContext context, CancellationToken cancellationToken);

    public abstract void Initialize(BffServer? server);
}
