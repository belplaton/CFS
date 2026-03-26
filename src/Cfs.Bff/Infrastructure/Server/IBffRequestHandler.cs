namespace Cfs.Bff.Infrastructure.Server;

public interface IBffRequestHandler
{
    string Pattern { get; }

    Task<BffHandlerResponse> HandleRequestAsync(HttpContext context, CancellationToken cancellationToken);

    void Initialize(BffServer? server);
}

public interface IBffRequestHandler<TBffRequestComposer, TBffRequestHandler> : IBffRequestHandler
    where TBffRequestComposer : BffRequestComposer<TBffRequestComposer, TBffRequestHandler>, new()
    where TBffRequestHandler : BffRequestHandler<TBffRequestComposer, TBffRequestHandler>
{
}
