using System.Collections.Concurrent;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Cfs.Contracts.Auth;

namespace Cfs.Bff.Auth;

internal sealed class InMemoryAuthGateway : IAuthGateway
{
    private readonly ConcurrentDictionary<string, UserSummary> _sessions = new(StringComparer.Ordinal);

    public ValueTask<AuthSessionResponse?> LoginAsync(LoginRequest request, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Email) || string.IsNullOrWhiteSpace(request.Password))
        {
            return ValueTask.FromResult<AuthSessionResponse?>(null);
        }

        var normalizedEmail = request.Email.Trim().ToLowerInvariant();
        var user = new UserSummary(
            CreateDeterministicUserId(normalizedEmail),
            normalizedEmail,
            BuildDisplayName(normalizedEmail));

        var token = Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant();
        _sessions[token] = user;

        var session = new AuthSessionResponse(
            token,
            DateTimeOffset.UtcNow.AddHours(8),
            user);

        return ValueTask.FromResult<AuthSessionResponse?>(session);
    }

    public bool TryGetUser(string? accessToken, out UserSummary? user)
    {
        if (string.IsNullOrWhiteSpace(accessToken))
        {
            user = null;
            return false;
        }

        return _sessions.TryGetValue(accessToken, out user);
    }

    private static Guid CreateDeterministicUserId(string email)
    {
        var hash = SHA256.HashData(Encoding.UTF8.GetBytes(email));
        return new Guid(hash[..16]);
    }

    private static string BuildDisplayName(string email)
    {
        var seed = email.Split('@', 2)[0]
            .Replace('.', ' ')
            .Replace('_', ' ')
            .Replace('-', ' ');

        return CultureInfo.InvariantCulture.TextInfo.ToTitleCase(seed);
    }
}
