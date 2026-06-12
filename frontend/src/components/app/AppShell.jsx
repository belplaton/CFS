import { Cloud, CreditCard, HardDrive, LogOut, ShieldCheck, Trash2 } from 'lucide-react'
import { useEffect } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useI18n } from '@/components/app/I18nProvider'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { formatBytes } from '@/lib/utils'
import { useAuthStore } from '@/store/auth-store'
import { useFileStore } from '@/store/file-store'

const navigation = [
  { to: '/app/files', key: 'files', icon: HardDrive },
  { to: '/app/trash', key: 'trash', icon: Trash2 },
  { to: '/app/security', key: 'security', icon: ShieldCheck },
  { to: '/app/billing', key: 'billing', icon: CreditCard },
]

function AppShell() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const logout = useAuthStore((state) => state.logout)
  const accessToken = useAuthStore((state) => state.accessToken)
  const refreshProfile = useAuthStore((state) => state.refreshProfile)
  const user = useAuthStore((state) => state.user)
  const bootstrap = useFileStore((state) => state.bootstrap)
  const quota = useFileStore((state) => state.quota)
  const quotaBytes = quota.total || user?.quotaBytes || 5 * 1024 * 1024 * 1024
  const plan = user?.plan ?? 'Free'
  const usedBytes = quota.used || user?.usedBytes || 0
  const usagePercent = Math.min(Math.round((usedBytes / Math.max(quotaBytes, 1)) * 100), 100)
  const remainingBytes = Math.max(quotaBytes - usedBytes, 0)
  const displayName = user?.full_name?.trim() || t('appShell.defaultUserName')
  const displayEmail = user?.email?.trim() || t('appShell.noEmail')

  useEffect(() => {
    if (!accessToken) {
      return
    }

    void (async () => {
      await refreshProfile()
      await bootstrap()
    })()
  }, [accessToken, bootstrap, refreshProfile])

  return (
    <div className="surface-grid min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen w-full max-w-[1480px] gap-6 px-4 py-4 md:px-6">
        <aside className="hidden w-64 shrink-0 rounded-xl border bg-background px-5 py-6 shadow-sm lg:flex lg:flex-col">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg border bg-muted">
              <Cloud className="h-5 w-5 text-foreground" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{t('appShell.brandEyebrow')}</p>
              <h1 className="text-base font-semibold">{t('appShell.brandTitle')}</h1>
            </div>
          </div>

          <div className="mt-8">
            <p className="mb-3 px-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">{t('appShell.navigation')}</p>
            <nav className="space-y-1">
              {navigation.map(({ to, key, icon: Icon }) => (
                <NavLink
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-3 rounded-lg border border-transparent px-3 py-2.5 text-sm transition-colors',
                      isActive ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                    )
                  }
                  key={to}
                  to={to}
                >
                  <Icon className="h-4 w-4" />
                  {t(`appShell.nav.${key}`)}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="mt-6 space-y-3 rounded-xl border bg-card p-4">
            <div className="border-b border-border/70 pb-3">
              <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{t('appShell.account')}</p>
              <p className="mt-2 truncate text-sm font-semibold text-foreground">{displayName}</p>
              <p className="truncate text-sm text-muted-foreground">{displayEmail}</p>
            </div>

            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{t('appShell.storage')}</p>
            <p className="text-lg font-semibold">{t('appShell.planLabel', { plan })}</p>
            <p className="text-sm text-muted-foreground">
              {t('appShell.usedOfQuota', { used: formatBytes(usedBytes), quota: formatBytes(quotaBytes) })}
            </p>

            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-primary transition-[width]" style={{ width: `${usagePercent}%` }} />
            </div>

            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>{t('appShell.remaining')}</span>
              <span>{formatBytes(remainingBytes)}</span>
            </div>

            <Button
              className="w-full"
              onClick={() => navigate('/app/billing')}
              variant="outline"
            >
              {t('appShell.getMoreStorage')}
            </Button>
          </div>

          <div className="mt-auto px-2">
            <Button
              className="w-full justify-center gap-2"
              onClick={() => logout()}
              variant="outline"
            >
              <LogOut className="h-4 w-4" />
              {t('appShell.logout')}
            </Button>
          </div>
        </aside>

        <div className="flex min-h-[calc(100vh-2rem)] flex-1 flex-col overflow-hidden rounded-xl border bg-background shadow-sm">
          <main className="flex-1 overflow-y-auto px-5 py-5 md:px-6 md:py-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export default AppShell

