namespace Cfs.Bff.Options;

public sealed class BackendServicesOptions
{
    public const string SectionName = "BackendServices";

    public string AuthBaseUrl { get; init; } = string.Empty;

    public string FileBaseUrl { get; init; } = string.Empty;

    public string StorageBaseUrl { get; init; } = string.Empty;
}
