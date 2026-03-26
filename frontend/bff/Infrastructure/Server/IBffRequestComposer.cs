namespace Cfs.Bff.Infrastructure.Server;

public interface IBffRequestComposer
{
    Task<IResult> ComposeAsync(HttpContext context);

    void Initialize(string pattern, BffServer server, WebApplication application);

    void AddHandler(IBffRequestHandler handler);

    bool RemoveHandler(Type handlerType);

    bool RemoveHandler(Type handlerType, out IBffRequestHandler? handler);

    int HandlersCount { get; }
}

public interface IBffRequestComposer<TBffRequestComposer, TBffRequestHandler> : IBffRequestComposer
    where TBffRequestComposer : BffRequestComposer<TBffRequestComposer, TBffRequestHandler>, new()
    where TBffRequestHandler : BffRequestHandler<TBffRequestComposer, TBffRequestHandler>
{
}
