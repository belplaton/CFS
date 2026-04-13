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
    <div className="surface-grid min-h-screen bg-background px-4 py-6 text-foreground md:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card px-6 py-5 shadow-sm">
          <div>
            <p className="text-xs text-muted-foreground">Cloud File Storage</p>
            <h1 className="mt-2 text-2xl font-semibold md:text-3xl">Frontend delivery workspace</h1>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button asChild className="px-5" variant="ghost">
              <Link to="/login">Войти</Link>
            </Button>
            <Button asChild className="px-5">
              <Link to={isAuthenticated ? '/app/files' : '/register'}>
                {isAuthenticated ? 'Открыть приложение' : 'Начать'}
              </Link>
            </Button>
          </div>
        </header>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-xl border bg-card p-8 shadow-sm md:p-12">
            <div className="inline-flex items-center gap-2 rounded-md border bg-muted px-3 py-1.5 text-sm text-muted-foreground">
              <Sparkles className="h-4 w-4" />
              Фронтенд адаптирован под текущий roadmap проекта
            </div>

            <h2 className="mt-8 max-w-4xl text-4xl font-semibold leading-tight text-balance md:text-6xl">
              Не очередной лендинг, а рабочая SPA-заготовка для облачного хранилища.
            </h2>

            <p className="mt-6 max-w-2xl text-base leading-8 text-muted-foreground md:text-lg">
              В репозитории backend ещё не дошёл до полноценного Auth/File/Preview слоя, поэтому
              фронтенд собран как интеграционный scaffold: реальные маршруты, экраны, state и UX
              для файлового менеджера уже готовы, а API можно подключать по мере появления
              endpoints.
            </p>

            <div className="mt-10 flex flex-wrap gap-3">
              <Button asChild className="px-6 py-6 text-base">
                <Link to={isAuthenticated ? '/app/files' : '/login'}>
                  Перейти к файловому менеджеру
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild className="px-6 py-6 text-base" variant="outline">
                <Link to="/app/security">Посмотреть security flow</Link>
              </Button>
            </div>
          </div>

          <div className="grid gap-6">
            <div className="rounded-xl border bg-card p-8 shadow-sm">
              <p className="text-xs text-muted-foreground">Current scope</p>
              <ul className="mt-6 space-y-4 text-sm leading-7 text-muted-foreground">
                <li className="flex gap-3">
                  <FolderTree className="mt-1 h-4 w-4 shrink-0 text-foreground" />
                  Файловый менеджер, навигация по папкам, поиск, сортировка, корзина и квоты.
                </li>
                <li className="flex gap-3">
                  <ShieldCheck className="mt-1 h-4 w-4 shrink-0 text-foreground" />
                  Auth screens, verify/reset flow и подготовленный раздел security/2FA.
                </li>
                <li className="flex gap-3">
                  <Search className="mt-1 h-4 w-4 shrink-0 text-foreground" />
                  Preview modal и integration-ready слой под File/Preview API.
                </li>
              </ul>
            </div>

            {pillars.map(({ description, icon: Icon, title }) => (
              <div
                className="rounded-xl border bg-card p-6 shadow-sm"
                key={title}
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border bg-muted">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-5 text-xl font-semibold">{title}</h3>
                <p className="mt-3 text-sm leading-7 text-muted-foreground">{description}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

export default LandingPage

