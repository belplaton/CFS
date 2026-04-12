import {
  ArrowRight,
  FolderTree,
  LockKeyhole,
  Search,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/auth-store'

const pillars = [
  {
    icon: UploadCloud,
    title: 'File workflow',
    description: 'Drag & drop, структура папок, корзина, preview-слой и квота уже сведены в единый UI.',
  },
  {
    icon: LockKeyhole,
    title: 'Auth foundation',
    description: 'Отдельные экраны для login, register, verify email, reset password и security settings.',
  },
  {
    icon: Search,
    title: 'Integration-ready',
    description: 'Компоненты подготовлены под Auth/File/Preview сервисы и не завязаны на текущий лендинг.',
  },
]

function LandingPage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(10,132,255,0.16),_transparent_26%),radial-gradient(circle_at_bottom_right,_rgba(245,158,11,0.18),_transparent_28%),linear-gradient(180deg,_#f7fbff,_#f8f2e8)] px-4 py-6 text-slate-950 md:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="flex flex-wrap items-center justify-between gap-4 rounded-[32px] border border-white/80 bg-white/75 px-6 py-5 shadow-[0_20px_60px_rgba(148,163,184,0.14)] backdrop-blur">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-sky-700">Cloud File Storage</p>
            <h1 className="mt-2 text-2xl font-semibold md:text-3xl">Frontend delivery workspace</h1>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button asChild className="rounded-full px-6" variant="ghost">
              <Link to="/login">Войти</Link>
            </Button>
            <Button asChild className="rounded-full px-6">
              <Link to={isAuthenticated ? '/app/files' : '/register'}>
                {isAuthenticated ? 'Открыть приложение' : 'Начать'}
              </Link>
            </Button>
          </div>
        </header>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="rounded-[40px] border border-white/80 bg-slate-950 p-8 text-white shadow-[0_35px_90px_rgba(15,23,42,0.24)] md:p-12">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-2 text-sm text-cyan-200">
              <Sparkles className="h-4 w-4" />
              Фронтенд адаптирован под текущий roadmap проекта
            </div>

            <h2 className="mt-8 max-w-4xl text-4xl font-semibold leading-tight md:text-6xl">
              Не очередной лендинг, а рабочая SPA-заготовка для облачного хранилища.
            </h2>

            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-300 md:text-lg">
              В репозитории backend ещё не дошёл до полноценного Auth/File/Preview слоя, поэтому
              фронтенд собран как интеграционный scaffold: реальные маршруты, экраны, state и UX
              для файлового менеджера уже готовы, а API можно подключать по мере появления
              endpoints.
            </p>

            <div className="mt-10 flex flex-wrap gap-3">
              <Button asChild className="rounded-full px-6 py-6 text-base">
                <Link to={isAuthenticated ? '/app/files' : '/login'}>
                  Перейти к файловому менеджеру
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild className="rounded-full px-6 py-6 text-base text-white hover:bg-white/20" variant="ghost">
                <Link to="/app/security">Посмотреть security flow</Link>
              </Button>
            </div>
          </div>

          <div className="grid gap-6">
            <div className="rounded-[32px] border border-white/80 bg-white/80 p-8 shadow-[0_20px_60px_rgba(148,163,184,0.14)]">
              <p className="text-xs uppercase tracking-[0.35em] text-sky-700">Current scope</p>
              <ul className="mt-6 space-y-4 text-sm leading-7 text-slate-700">
                <li className="flex gap-3">
                  <FolderTree className="mt-1 h-4 w-4 shrink-0 text-sky-700" />
                  Файловый менеджер, навигация по папкам, поиск, сортировка, корзина и квоты.
                </li>
                <li className="flex gap-3">
                  <ShieldCheck className="mt-1 h-4 w-4 shrink-0 text-sky-700" />
                  Auth screens, verify/reset flow и подготовленный раздел security/2FA.
                </li>
                <li className="flex gap-3">
                  <Search className="mt-1 h-4 w-4 shrink-0 text-sky-700" />
                  Preview modal и integration-ready слой под File/Preview API.
                </li>
              </ul>
            </div>

            {pillars.map(({ description, icon: Icon, title }) => (
              <div
                className="rounded-[32px] border border-white/80 bg-white/80 p-6 shadow-[0_20px_60px_rgba(148,163,184,0.14)]"
                key={title}
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-5 text-xl font-semibold">{title}</h3>
                <p className="mt-3 text-sm leading-7 text-slate-600">{description}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

export default LandingPage

