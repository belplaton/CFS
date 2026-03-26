using Cfs.Bff.Auth;
using Cfs.Bff.Files;
using Cfs.Bff.Options;

namespace Cfs.Bff.Infrastructure;

public static class BackendGatewayServiceCollectionExtensions
{
    public static IServiceCollection AddBackendGateways(this IServiceCollection services, BackendServicesOptions options)
    {
        if (options.Mode == BackendServiceMode.Mock)
        {
            services.AddSingleton<IAuthGateway, InMemoryAuthGateway>();
            services.AddSingleton<IWorkspaceGateway, InMemoryWorkspaceGateway>();
            return services;
        }

        services.AddHttpClient<RemoteAuthGateway>(client =>
        {
            client.BaseAddress = BuildBaseUri(options.Auth.BaseUrl, "auth");
            client.Timeout = TimeSpan.FromSeconds(15);
        });
        services.AddTransient<IAuthGateway>(serviceProvider => serviceProvider.GetRequiredService<RemoteAuthGateway>());

        services.AddHttpClient<RemoteWorkspaceGateway>(client =>
        {
            client.BaseAddress = BuildBaseUri(options.Files.BaseUrl, "files");
            client.Timeout = TimeSpan.FromSeconds(15);
        });
        services.AddTransient<IWorkspaceGateway>(
            serviceProvider => serviceProvider.GetRequiredService<RemoteWorkspaceGateway>());

        return services;
    }

    private static Uri BuildBaseUri(string? baseUrl, string serviceName)
    {
        if (Uri.TryCreate(baseUrl, UriKind.Absolute, out var uri))
        {
            return uri;
        }

        throw new InvalidOperationException(
            $"BackendServices:{serviceName}:BaseUrl must be an absolute URL when running in remote mode.");
    }
}
