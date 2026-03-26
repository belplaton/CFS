using Cfs.Contracts.Auth;

namespace Cfs.Bff.Auth;

public interface IAuthGateway
{
    ValueTask<AuthSessionResponse> LoginAsync(LoginRequest request, CancellationToken cancellationToken);

    ValueTask<UserSummary?> GetCurrentUserAsync(string? accessToken, CancellationToken cancellationToken);
}
