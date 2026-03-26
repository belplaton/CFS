using System.Text.Json.Serialization;
using Cfs.Bff.Auth;
using Cfs.Bff.Files;
using Cfs.Bff.Handlers.Get;
using Cfs.Bff.Handlers.Post;
using Cfs.Bff.Infrastructure;
using Cfs.Bff.Infrastructure.Server;
using Cfs.Bff.Options;

var builder = WebApplication.CreateBuilder(args);
var backendServicesOptions = builder.Configuration
    .GetSection(BackendServicesOptions.SectionName)
    .Get<BackendServicesOptions>() ?? new BackendServicesOptions();

builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.Converters.Add(new JsonStringEnumConverter());
});

builder.Services.Configure<BackendServicesOptions>(
    builder.Configuration.GetSection(BackendServicesOptions.SectionName));

var allowedOrigins = builder.Configuration
    .GetSection("Cors:AllowedOrigins")
    .Get<string[]>() ?? [];

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
