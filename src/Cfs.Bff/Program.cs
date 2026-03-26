using System.Text.Json.Serialization;
using Cfs.Bff.Auth;
using Cfs.Bff.Files;
using Cfs.Bff.Infrastructure;
using Cfs.Bff.Options;
using Cfs.Contracts.Auth;
using Cfs.Contracts.Common;
using Cfs.Contracts.Files;
using Cfs.Contracts.System;
using Microsoft.Extensions.Options;

var builder = WebApplication.CreateBuilder(args);

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

builder.Services.AddSingleton<IAuthGateway, InMemoryAuthGateway>();
builder.Services.AddSingleton<IWorkspaceGateway, InMemoryWorkspaceGateway>();

var app = builder.Build();

if (allowedOrigins.Length > 0)
{
    app.UseCors("Frontend");
}

app.MapGet("/", () => Results.Redirect("/api/health"));

var api = app.MapGroup("/api");

api.MapGet("/health", (IOptions<BackendServicesOptions> options) =>
{
    var current = options.Value;

    return TypedResults.Ok(new ApiHealthResponse(
        "ok",
        DateTimeOffset.UtcNow,
        new Dictionary<string, string>
        {
            ["auth"] = current.AuthBaseUrl,
            ["files"] = current.FileBaseUrl,
            ["storage"] = current.StorageBaseUrl
        }));
});

var auth = api.MapGroup("/auth");

auth.MapPost("/login",
    async (
        LoginRequest request,
        IAuthGateway gateway,
        CancellationToken cancellationToken) =>
    {
        var session = await gateway.LoginAsync(request, cancellationToken);

        return session is null
            ? Results.BadRequest(new ApiError(
                "auth.invalid_credentials",
                "Email and password are required."))
            : Results.Ok(session);
    });

auth.MapGet("/me",
    (
        HttpContext context,
        IAuthGateway gateway) =>
    {
        return gateway.TryGetUser(context.TryGetBearerToken(), out var user) && user is not null
            ? Results.Ok(user)
            : Results.Unauthorized();
    });

var files = api.MapGroup("/files");

files.MapGet("/root",
    async (
        HttpContext context,
        IAuthGateway authGateway,
        IWorkspaceGateway workspaceGateway,
        CancellationToken cancellationToken) =>
    {
        if (!authGateway.TryGetUser(context.TryGetBearerToken(), out var user) || user is null)
        {
            return Results.Unauthorized();
        }

        var response = await workspaceGateway.GetRootAsync(user.Id, cancellationToken);
        return Results.Ok(response);
    });

var folders = api.MapGroup("/folders");

folders.MapPost(string.Empty,
    async (
        HttpContext context,
        CreateFolderRequest request,
        IAuthGateway authGateway,
        IWorkspaceGateway workspaceGateway,
        CancellationToken cancellationToken) =>
    {
        if (!authGateway.TryGetUser(context.TryGetBearerToken(), out var user) || user is null)
        {
            return Results.Unauthorized();
        }

        try
        {
            var response = await workspaceGateway.CreateFolderAsync(user.Id, request, cancellationToken);
            return Results.Ok(response);
        }
        catch (InvalidOperationException exception)
        {
            return Results.BadRequest(new ApiError("folders.invalid_request", exception.Message));
        }
    });

app.Run();
