using Cfs.Contracts.Auth;

namespace Cfs.Frontend.Services;

public sealed class SessionCoordinator(SessionState sessionState, BrowserSessionStore browserSessionStore)
{
    public ValueTask<AuthSessionResponse?> GetStoredSessionAsync() =>
        browserSessionStore.GetAsync();

    public async ValueTask SignInAsync(AuthSessionResponse session)
    {
        sessionState.SetSession(session);
        await browserSessionStore.SaveAsync(session);
    }

    public async ValueTask UpdateUserAsync(UserSummary user)
    {
        sessionState.UpdateUser(user);

        if (sessionState.Session is not null)
        {
            await browserSessionStore.SaveAsync(sessionState.Session);
        }
    }

    public async ValueTask SignOutAsync(
        string? noticeMessage = null,
        SessionNoticeLevel level = SessionNoticeLevel.Info)
    {
        await browserSessionStore.ClearAsync();
        sessionState.ClearSession(noticeMessage, level);
    }
}
