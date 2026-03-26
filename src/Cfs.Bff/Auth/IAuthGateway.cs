using Cfs.Contracts.Auth;

namespace Cfs.Bff.Auth;

public interface IAuthGateway
{
    ValueTask<AuthSessionResponse?> LoginAsync(LoginRequest request, CancellationToken cancellationToken);

    bool TryGetUser(string? accessToken, out UserSummary? user);
}
