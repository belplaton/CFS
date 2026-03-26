namespace Cfs.Bff.Infrastructure.Http;

public sealed class UpstreamApiException : Exception
{
    public UpstreamApiException(
        int statusCode,
        string code,
        string message,
        string serviceName,
        Exception? innerException = null) : base(message, innerException)
    {
        StatusCode = statusCode;
        Code = code;
        ServiceName = serviceName;
    }

    public int StatusCode { get; }

    public string Code { get; }

    public string ServiceName { get; }
}
