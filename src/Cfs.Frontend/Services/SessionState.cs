using Cfs.Contracts.Auth;

namespace Cfs.Frontend.Services;

public sealed class SessionState
{
    public event Action? Changed;

    public AuthSessionResponse? Session { get; private set; }

    public bool IsAuthenticated => Session is not null;

    public string? AccessToken => Session?.AccessToken;

    public UserSummary? User => Session?.User;

    public void SetSession(AuthSessionResponse session)
    {
        Session = session;
        Changed?.Invoke();
    }

    public void Clear()
    {
        Session = null;
        Changed?.Invoke();
    }
}
