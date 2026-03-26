using System.Text.Json.Serialization;
using Cfs.Bff.Auth;
using Cfs.Bff.Files;
using Cfs.Bff.Handlers.Get;
using Cfs.Bff.Handlers.Post;
using Cfs.Bff.Infrastructure;
using Cfs.Bff.Infrastructure.Server;
using Cfs.Bff.Options;
using Microsoft.Extensions.Options;

var builder = WebApplication.CreateBuilder(args);
var backendServicesOptions = BuildBackendServicesOptions(builder.Configuration);
var allowedOrigins = ReadAllowedOrigins(builder.Configuration);

builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.Converters.Add(new JsonStringEnumConverter());
});

builder.Services.AddSingleton<IOptions<BackendServicesOptions>>(Options.Create(backendServicesOptions));

builder.Services.AddCors(options =>
{
    options.AddPolicy("Frontend", policy =>
    {
        if (allowedOrigins.Length == 0)
        {
            return;
        }

        policy
            .WithOrigins(allowedOrigins)
            .AllowAnyHeader()
            .AllowAnyMethod();
    });
});

builder.Services.AddBackendGateways(backendServicesOptions);

var app = builder.Build();
var server = new BffServer(app);

if (allowedOrigins.Length > 0)
{
    app.UseCors("Frontend");
}

app.MapGet("/", () => Results.Redirect("/api/health"));

server
    .RegisterRequestHandler<BffGetComposer, BffGetHandler, HealthGetHandler>()
    .RegisterRequestHandler<BffGetComposer, BffGetHandler, CurrentUserGetHandler>()
    .RegisterRequestHandler<BffGetComposer, BffGetHandler, RootFilesGetHandler>()
    .RegisterRequestHandler<BffPostComposer, BffPostHandler, LoginPostHandler>()
    .RegisterRequestHandler<BffPostComposer, BffPostHandler, CreateFolderPostHandler>();

app.Run();

static string[] ReadAllowedOrigins(IConfiguration configuration)
{
    var configuredOrigins = configuration
        .GetSection("Cors:AllowedOrigins")
        .Get<string[]>() ?? [];

    var envOrigins = Environment.GetEnvironmentVariable("CORS_ALLOWED_ORIGINS");
    if (string.IsNullOrWhiteSpace(envOrigins))
    {
        return configuredOrigins;
    }

    return envOrigins.Split(
        ',',
        StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
}

static BackendServicesOptions BuildBackendServicesOptions(IConfiguration configuration)
{
    var configuredOptions = configuration
        .GetSection(BackendServicesOptions.SectionName)
        .Get<BackendServicesOptions>() ?? new BackendServicesOptions();

    return new BackendServicesOptions
    {
        Mode = ReadMode(configuredOptions.Mode),
        Auth = new AuthServiceOptions
        {
            BaseUrl = ReadServiceUrl("AUTH_SERVICE_URL", configuredOptions.Auth.BaseUrl),
            LoginPath = configuredOptions.Auth.LoginPath,
            CurrentUserPath = configuredOptions.Auth.CurrentUserPath
        },
        Files = new FileServiceOptions
        {
            BaseUrl = ReadServiceUrl("FILE_SERVICE_URL", configuredOptions.Files.BaseUrl),
            RootPath = configuredOptions.Files.RootPath,
            CreateFolderPath = configuredOptions.Files.CreateFolderPath
        },
        Storage = new StorageServiceOptions
        {
            BaseUrl = ReadServiceUrl("STORAGE_SERVICE_URL", configuredOptions.Storage.BaseUrl)
        }
    };
}

static BackendServiceMode ReadMode(BackendServiceMode configuredMode)
{
    var modeFromEnvironment = Environment.GetEnvironmentVariable("BACKEND_SERVICES_MODE");
    if (Enum.TryParse<BackendServiceMode>(modeFromEnvironment, true, out var parsedMode))
    {
        return parsedMode;
    }

    var useMockGateways = Environment.GetEnvironmentVariable("USE_MOCK_GATEWAYS");
    if (bool.TryParse(useMockGateways, out var useMock))
    {
        return useMock ? BackendServiceMode.Mock : BackendServiceMode.Remote;
    }

    return configuredMode;
}

static string ReadServiceUrl(string environmentVariable, string configuredValue)
{
    var fromEnvironment = Environment.GetEnvironmentVariable(environmentVariable);
    if (string.IsNullOrWhiteSpace(fromEnvironment))
    {
        return configuredValue;
    }

    return fromEnvironment.Trim().TrimEnd('/');
}
