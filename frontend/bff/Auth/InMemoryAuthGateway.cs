using System.Collections.Concurrent;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Cfs.Contracts.Auth;

namespace Cfs.Bff.Auth;

internal sealed class InMemoryAuthGateway : IAuthGateway
{
    private readonly ConcurrentDictionary<string, UserSummary> _sessions = new(StringComparer.Ordinal);

    public ValueTask<AuthSessionResponse> LoginAsync(LoginRequest request, CancellationToken cancellationToken)
    {
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

        return ValueTask.FromResult(session);
    }

    public ValueTask<UserSummary?> GetCurrentUserAsync(string? accessToken, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(accessToken))
        {
            return ValueTask.FromResult<UserSummary?>(null);
        }

        _sessions.TryGetValue(accessToken, out var user);
        return ValueTask.FromResult(user);
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
