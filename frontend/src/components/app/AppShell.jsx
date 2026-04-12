import { Cloud, HardDrive, LogOut, ShieldCheck, Trash2 } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

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
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(10,132,255,0.18),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(245,158,11,0.16),_transparent_28%),linear-gradient(180deg,_#f6fbff,_#f4efe5)] text-slate-950">
      <div className="mx-auto flex min-h-screen w-full max-w-[1560px] gap-6 px-4 py-4 md:px-6">
        <aside className="hidden w-80 shrink-0 rounded-[28px] border border-white/70 bg-slate-950 px-6 py-7 text-white shadow-[0_30px_80px_rgba(15,23,42,0.24)] lg:flex lg:flex-col">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10">
              <Cloud className="h-6 w-6 text-cyan-300" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Frontend Sprint</p>
              <h1 className="text-xl font-semibold">Cloud File Storage</h1>
            </div>
          </div>

          <div className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-5">
            <p className="text-sm text-slate-300">Текущий фронтенд-срез</p>
            <p className="mt-2 text-2xl font-semibold">Auth + File Manager</p>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              SPA подготовлена под интеграцию с Auth/File/Preview сервисами. Пока backend
              ограничен заглушками, интерфейс работает поверх локального store.
            </p>
          </div>

          <nav className="mt-8 space-y-2">
            {navigation.map(({ to, label, icon: Icon }) => (
              <NavLink
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition',
                    isActive ? 'bg-white text-slate-950' : 'text-slate-300 hover:bg-white/10 hover:text-white',
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

          <div className="mt-auto rounded-3xl border border-white/10 bg-white/5 p-5">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-500 font-semibold text-slate-950">
                {getInitials(user?.fullName)}
              </div>
              <div className="min-w-0">
                <p className="truncate font-medium">{user?.fullName}</p>
                <p className="truncate text-sm text-slate-300">{user?.email}</p>
              </div>
            </div>
            <Button
              className="mt-5 w-full justify-center gap-2 bg-white/10 text-white hover:bg-white/20"
              onClick={() => {
                logout()
                navigate('/login')
              }}
              variant="ghost"
            >
              <LogOut className="h-4 w-4" />
              Выйти
            </Button>
          </div>
        </aside>

        <div className="flex min-h-[calc(100vh-2rem)] flex-1 flex-col overflow-hidden rounded-[32px] border border-white/70 bg-white/80 shadow-[0_30px_80px_rgba(148,163,184,0.18)] backdrop-blur">
          <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/80 px-5 py-4 md:px-8">
            <div className="flex items-center gap-3 lg:hidden">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-950 text-white">
                <Cloud className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-sky-700">Cloud Storage</p>
                <p className="font-semibold">Frontend Workspace</p>
              </div>
            </div>
            <div className="rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900">
              Mock mode для UI-интеграции до готовности API
            </div>
          </header>

          <main className="flex-1 overflow-y-auto px-5 py-5 md:px-8 md:py-8">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export default AppShell

