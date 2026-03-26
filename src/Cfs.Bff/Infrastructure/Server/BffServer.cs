using System.Collections.Concurrent;

namespace Cfs.Bff.Infrastructure.Server;

public sealed class BffServer(WebApplication application)
{
    private readonly ConcurrentDictionary<Type, string> _registeredRequestHandlers = new();
    private readonly ConcurrentDictionary<string, Dictionary<Type, IBffRequestComposer>> _registeredRequestComposers =
        new(StringComparer.Ordinal);

    public WebApplication Application { get; } = application;

    public BffServer RegisterRequestHandler<TBffRequestComposer, TBaseBffRequestHandler, TRealBffRequestHandler>()
        where TBffRequestComposer : BffRequestComposer<TBffRequestComposer, TBaseBffRequestHandler>, new()
        where TBaseBffRequestHandler : BffRequestHandler<TBffRequestComposer, TBaseBffRequestHandler>
        where TRealBffRequestHandler : class, TBaseBffRequestHandler
    {
        var handlerType = typeof(TRealBffRequestHandler);
        var composerType = typeof(TBffRequestComposer);
        if (_registeredRequestHandlers.ContainsKey(handlerType))
        {
            return this;
        }

        var handler = ActivatorUtilities.CreateInstance<TRealBffRequestHandler>(Application.Services);
        handler.Initialize(this);
        _registeredRequestHandlers[handlerType] = handler.Pattern;

        if (!_registeredRequestComposers.TryGetValue(handler.Pattern, out var composers))
        {
            composers = new Dictionary<Type, IBffRequestComposer>();
            _registeredRequestComposers[handler.Pattern] = composers;
        }

        TBffRequestComposer composer;
        if (!composers.TryGetValue(composerType, out var composerRaw))
        {
            composer = new TBffRequestComposer();
            composer.Initialize(handler.Pattern, this, Application);
            composers[composerType] = composer;
        }
        else
        {
            composer = (TBffRequestComposer)composerRaw;
        }

        composer.AddHandler(handler);
        return this;
    }
}
