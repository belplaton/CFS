using Cfs.Contracts.Common;

namespace Cfs.Bff.Infrastructure.Http;

internal static class UpstreamApiExceptionExtensions
{
    public static IResult ToResult(this UpstreamApiException exception)
    {
        var error = new ApiError(exception.Code, exception.Message);

        return exception.StatusCode switch
        {
            StatusCodes.Status400BadRequest => Results.BadRequest(error),
            StatusCodes.Status401Unauthorized => Results.Json(error, statusCode: StatusCodes.Status401Unauthorized),
            StatusCodes.Status403Forbidden => Results.Json(error, statusCode: StatusCodes.Status403Forbidden),
            StatusCodes.Status404NotFound => Results.NotFound(error),
            StatusCodes.Status409Conflict => Results.Json(error, statusCode: StatusCodes.Status409Conflict),
            StatusCodes.Status422UnprocessableEntity => Results.Json(
                error,
                statusCode: StatusCodes.Status422UnprocessableEntity),
            StatusCodes.Status503ServiceUnavailable => Results.Json(
                error,
                statusCode: StatusCodes.Status503ServiceUnavailable),
            _ when exception.StatusCode >= StatusCodes.Status500InternalServerError => Results.Json(
                new ApiError(
                    $"{exception.ServiceName}.unavailable",
                    $"{exception.ServiceName} service is unavailable."),
                statusCode: StatusCodes.Status502BadGateway),
            _ => Results.Json(error, statusCode: StatusCodes.Status502BadGateway)
        };
    }
}
