using Cfs.Contracts.Auth;

namespace Cfs.Frontend.Services;

public sealed class SessionState
{
    public event Action? Changed;

    public AuthSessionResponse? Session { get; private set; }

    public SessionNotice? Notice { get; private set; }

    public bool IsRestoring { get; private set; }

    public bool IsReady { get; private set; }

    public bool IsAuthenticated =>
        Session is { } session &&
        session.ExpiresAtUtc > DateTimeOffset.UtcNow;

    public string? AccessToken => IsAuthenticated ? Session?.AccessToken : null;

    public UserSummary? User => IsAuthenticated ? Session?.User : null;

    public void BeginRestore()
    {
        IsRestoring = true;
        IsReady = false;
        NotifyChanged();
    }

    public void CompleteRestore()
    {
        IsRestoring = false;
        IsReady = true;
        NotifyChanged();
    }

    public void SetSession(AuthSessionResponse session, bool clearNotice = true)
    {
        Session = session;

        if (clearNotice)
        {
            Notice = null;
        }

        NotifyChanged();
    }

    public void UpdateUser(UserSummary user, bool clearNotice = false)
    {
        if (Session is null)
        {
            return;
        }

        Session = Session with
        {
            User = user
        };

        if (clearNotice)
        {
            Notice = null;
        }

        NotifyChanged();
    }

    public void SetNotice(string message, SessionNoticeLevel level = SessionNoticeLevel.Info)
    {
        Notice = new SessionNotice(message, level);
        NotifyChanged();
    }

    public void ClearNotice()
    {
        if (Notice is null)
        {
            return;
        }

        Notice = null;
        NotifyChanged();
    }

    public void ClearSession(string? noticeMessage = null, SessionNoticeLevel level = SessionNoticeLevel.Info)
    {
        Session = null;
        Notice = string.IsNullOrWhiteSpace(noticeMessage)
            ? null
            : new SessionNotice(noticeMessage, level);

        NotifyChanged();
    }

    private void NotifyChanged()
    {
        Changed?.Invoke();
    }
}

public sealed record SessionNotice(string Message, SessionNoticeLevel Level);

public enum SessionNoticeLevel
{
    Info = 0,
    Warning = 1,
    Error = 2
}
