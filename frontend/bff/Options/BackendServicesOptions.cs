namespace Cfs.Bff.Options;

public sealed class BackendServicesOptions
{
    public const string SectionName = "BackendServices";

    public BackendServiceMode Mode { get; init; } = BackendServiceMode.Mock;

    public AuthServiceOptions Auth { get; init; } = new();

    public FileServiceOptions Files { get; init; } = new();

    public StorageServiceOptions Storage { get; init; } = new();
}

public enum BackendServiceMode
{
    Mock = 0,
    Remote = 1
}

public sealed class AuthServiceOptions
{
    public string BaseUrl { get; init; } = string.Empty;

    public string LoginPath { get; init; } = "/api/auth/login";

    public string CurrentUserPath { get; init; } = "/api/auth/me";
}

public sealed class FileServiceOptions
{
    public string BaseUrl { get; init; } = string.Empty;

    public string RootPath { get; init; } = "/api/files/root";

    public string CreateFolderPath { get; init; } = "/api/folders";
}

public sealed class StorageServiceOptions
{
    public string BaseUrl { get; init; } = string.Empty;
}
