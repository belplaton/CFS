using System.Text.Json.Serialization;
using Cfs.Bff.Auth;
using Cfs.Bff.Files;
using Cfs.Bff.Handlers.Get;
using Cfs.Bff.Handlers.Post;
using Cfs.Bff.Infrastructure;
using Cfs.Bff.Infrastructure.Server;
using Cfs.Bff.Options;

var builder = WebApplication.CreateBuilder(args);

builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.Converters.Add(new JsonStringEnumConverter());
});

// Чтение конфигурации BackendServices с поддержкой ENV переменных
builder.Services.Configure<BackendServicesOptions>(options =>
{
    builder.Configuration.GetSection(BackendServicesOptions.SectionName).Bind(options);
    
    // Переопределяем из ENV переменных если заданы (для Docker)
    var authUrl = Environment.GetEnvironmentVariable("AUTH_SERVICE_URL");
    var fileUrl = Environment.GetEnvironmentVariable("FILE_SERVICE_URL");
    var storageUrl = Environment.GetEnvironmentVariable("STORAGE_SERVICE_URL");
    
    if (!string.IsNullOrWhiteSpace(authUrl))
        options.AuthBaseUrl = authUrl.TrimEnd('/');
    if (!string.IsNullOrWhiteSpace(fileUrl))
        options.FileBaseUrl = fileUrl.TrimEnd('/');
    if (!string.IsNullOrWhiteSpace(storageUrl))
        options.StorageBaseUrl = storageUrl.TrimEnd('/');
});

var allowedOrigins = builder.Configuration
    .GetSection("Cors:AllowedOrigins")
    .Get<string[]>() ?? [];

// Поддержка ENV переменной для CORS (для Docker)
var corsOriginsEnv = Environment.GetEnvironmentVariable("CORS_ALLOWED_ORIGINS");
if (!string.IsNullOrWhiteSpace(corsOriginsEnv))
{
    allowedOrigins = corsOriginsEnv.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
}

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

// Чтение флага использования mock gateway
var useMockGateways = builder.Configuration.GetValue<bool>("UseMockGateways");
var useMockGatewaysEnv = Environment.GetEnvironmentVariable("USE_MOCK_GATEWAYS");
if (!string.IsNullOrWhiteSpace(useMockGatewaysEnv))
{
    useMockGateways = bool.Parse(useMockGatewaysEnv);
}

// Регистрация HttpClient для внешних сервисов
builder.Services.AddHttpClient("BackendServices", client =>
{
    client.DefaultRequestHeaders.Accept.Add(new System.Net.Http.Headers.MediaTypeWithQualityHeaderValue("application/json"));
});

if (useMockGateways)
{
    builder.Services.AddSingleton<IAuthGateway, InMemoryAuthGateway>();
    builder.Services.AddSingleton<IWorkspaceGateway, InMemoryWorkspaceGateway>();
}
else
{
    // Real gateways требуют HttpClient из factory
    builder.Services.AddSingleton<IAuthGateway>(sp =>
    {
        var options = sp.GetRequiredService<IOptions<BackendServicesOptions>>();
        var httpClientFactory = sp.GetRequiredService<IHttpClientFactory>();
        return new RealAuthGateway(options, httpClientFactory.CreateClient("BackendServices"));
    });
    
    builder.Services.AddSingleton<IWorkspaceGateway>(sp =>
    {
        var options = sp.GetRequiredService<IOptions<BackendServicesOptions>>();
        var httpClientFactory = sp.GetRequiredService<IHttpClientFactory>();
        return new RealWorkspaceGateway(options, httpClientFactory.CreateClient("BackendServices"));
    });
}

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
