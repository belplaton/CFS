import { Cloud } from 'lucide-react'
import { Link } from 'react-router-dom'

import ThemeSwitcher from '@/components/app/ThemeSwitcher'

function AuthShell({ eyebrow, title, description, footer, children }) {
  return (
    <div className="surface-grid min-h-screen bg-background px-4 py-10 text-foreground md:px-8">
      <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1fr_420px]">
        <div className="rounded-xl border bg-card p-8 shadow-sm md:p-10">
          <div className="flex items-start justify-between gap-4">
            <Link className="inline-flex items-center gap-3" to="/">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border bg-muted">
                <Cloud className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Cloud File Storage</p>
                <p className="font-semibold">shadcn/ui frontend</p>
              </div>
            </Link>
            <ThemeSwitcher compact />
          </div>

          <p className="mt-10 text-sm text-muted-foreground">{eyebrow}</p>
          <h1 className="mt-3 max-w-2xl text-4xl font-semibold leading-tight md:text-5xl">{title}</h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-muted-foreground">{description}</p>

          <div className="mt-10 grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border bg-muted/40 p-5">
              <p className="text-sm text-muted-foreground">Что уже отражено в UI</p>
              <p className="mt-3 text-lg font-medium">Роутинг, auth flow, file manager, trash, quota, security</p>
            </div>
            <div className="rounded-lg border bg-muted/40 p-5">
              <p className="text-sm text-muted-foreground">Чего ждём от backend</p>
              <p className="mt-3 text-lg font-medium">Реальные endpoints Auth/File/Preview и upload pipeline</p>
            </div>
          </div>
        </div>

        <div className="rounded-xl border bg-card p-6 shadow-sm md:p-8">
          {children}
          {footer ? <div className="mt-6 text-sm text-muted-foreground">{footer}</div> : null}
        </div>
      </div>
    </div>
  )
}

export default AuthShell

