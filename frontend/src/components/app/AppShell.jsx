import { Cloud, HardDrive, LogOut, ShieldCheck, Trash2 } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import { Button } from '@/components/ui/button'
import { cn, getInitials } from '@/lib/utils'
import { useAuthStore } from '@/store/auth-store'

const navigation = [
  { to: '/app/files', label: 'Файлы', icon: HardDrive },
  { to: '/app/trash', label: 'Корзина', icon: Trash2 },
  { to: '/app/security', label: 'Безопасность', icon: ShieldCheck },
]

function AppShell() {
  const navigate = useNavigate()
  const { logout, user } = useAuthStore((state) => ({
    logout: state.logout,
    user: state.user,
  }))

  return (
    <div className="surface-grid min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen w-full max-w-[1480px] gap-6 px-4 py-4 md:px-6">
        <aside className="hidden w-72 shrink-0 rounded-xl border bg-background px-5 py-6 shadow-sm lg:flex lg:flex-col">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg border bg-muted">
              <Cloud className="h-5 w-5 text-foreground" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Workspace</p>
              <h1 className="text-base font-semibold">Cloud File Storage</h1>
            </div>
          </div>

          <div className="mt-6 rounded-xl border bg-muted/50 p-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Current slice</p>
            <p className="mt-2 text-lg font-semibold">Auth + File Manager</p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              SPA подготовлена под интеграцию с Auth/File/Preview сервисами. Пока backend
              ограничен заглушками, интерфейс работает поверх локального store.
            </p>
          </div>

          <div className="mt-8">
            <p className="mb-3 px-2 text-xs uppercase tracking-[0.2em] text-muted-foreground">Navigation</p>
            <nav className="space-y-1">
              {navigation.map(({ to, label, icon: Icon }) => (
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
                  {label}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="mt-auto rounded-xl border bg-muted/50 p-4">
            <div className="flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border bg-background font-semibold">
                {getInitials(user?.fullName)}
              </div>
              <div className="min-w-0">
                <p className="truncate font-medium">{user?.fullName}</p>
                <p className="truncate text-sm text-muted-foreground">{user?.email}</p>
              </div>
            </div>
            <Button
              className="mt-4 w-full justify-center gap-2"
              onClick={() => {
                logout()
                navigate('/login')
              }}
              variant="outline"
            >
              <LogOut className="h-4 w-4" />
              Выйти
            </Button>
          </div>
        </aside>

        <div className="flex min-h-[calc(100vh-2rem)] flex-1 flex-col overflow-hidden rounded-xl border bg-background shadow-sm">
          <header className="flex flex-wrap items-center justify-between gap-3 border-b bg-card px-5 py-4 md:px-6">
            <div className="flex items-center gap-3 lg:hidden">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border bg-muted">
                <Cloud className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Cloud Storage</p>
                <p className="font-semibold">Workspace</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="rounded-md border bg-muted px-3 py-1.5 text-sm text-muted-foreground">
                Mock mode для UI-интеграции до готовности API
              </div>
              <ThemeSwitcher compact />
              <div className="hidden rounded-md border bg-card px-3 py-1.5 text-sm text-muted-foreground md:block">
                {user?.email}
              </div>
            </div>
          </header>

          <main className="flex-1 overflow-y-auto px-5 py-5 md:px-6 md:py-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export default AppShell

