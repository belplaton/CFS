namespace Cfs.Bff.Infrastructure.Server;

public abstract class BffRequestComposer<TBffRequestComposer, TBffRequestHandler> :
    IBffRequestComposer<TBffRequestComposer, TBffRequestHandler>
    where TBffRequestComposer : BffRequestComposer<TBffRequestComposer, TBffRequestHandler>, new()
    where TBffRequestHandler : BffRequestHandler<TBffRequestComposer, TBffRequestHandler>
{
    private readonly Dictionary<Type, IBffRequestHandler> _handlers = [];

    protected IReadOnlyDictionary<Type, IBffRequestHandler> Handlers => _handlers;

    public int HandlersCount => _handlers.Count;

    public Task<IResult> ComposeAsync(HttpContext context) =>
        _handlers.Count > 0
            ? ComposeAsyncInternal(context, context.RequestAborted)
            : Task.FromResult<IResult>(Results.NotFound());

    protected abstract Task<IResult> ComposeAsyncInternal(HttpContext context, CancellationToken cancellationToken);

    public abstract void Initialize(string pattern, BffServer server, WebApplication application);

    public void AddHandler(IBffRequestHandler handler)
    {
        var handlerType = handler.GetType();
        if (!typeof(TBffRequestHandler).IsAssignableFrom(handlerType))
        {
            throw new ArgumentException(
                $"Type '{handlerType}' does not implement '{typeof(TBffRequestHandler)}'.");
        }

        _handlers.Add(handlerType, handler);
    }

    public bool RemoveHandler(Type handlerType)
    {
        if (!typeof(TBffRequestHandler).IsAssignableFrom(handlerType))
        {
            throw new ArgumentException(
                $"Type '{handlerType}' does not implement '{typeof(TBffRequestHandler)}'.");
        }

        return _handlers.Remove(handlerType);
    }

    public bool RemoveHandler(Type handlerType, out IBffRequestHandler? handler)
    {
        if (!typeof(TBffRequestHandler).IsAssignableFrom(handlerType))
        {
            throw new ArgumentException(
                $"Type '{handlerType}' does not implement '{typeof(TBffRequestHandler)}'.");
        }

        return _handlers.Remove(handlerType, out handler);
    }

    protected async Task<IResult> ExecuteHandlersAsync(HttpContext context, CancellationToken cancellationToken)
    {
        IResult? finalResult = null;

        foreach (var handler in _handlers.Values)
        {
            finalResult = (await handler.HandleRequestAsync(context, cancellationToken)).Result;
        }

        return finalResult ?? Results.NotFound();
    }
}
