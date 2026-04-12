import { Cloud } from 'lucide-react'
import { Link } from 'react-router-dom'

function AuthShell({ eyebrow, title, description, footer, children }) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(34,197,94,0.12),_transparent_24%),radial-gradient(circle_at_left,_rgba(14,165,233,0.16),_transparent_24%),linear-gradient(180deg,_#fbfdff,_#eff6ff_48%,_#f7f1e7)] px-4 py-10 text-slate-950 md:px-8">
      <div className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-[32px] border border-white/80 bg-slate-950 p-8 text-white shadow-[0_30px_90px_rgba(15,23,42,0.22)] md:p-10">
          <Link className="inline-flex items-center gap-3" to="/">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10">
              <Cloud className="h-6 w-6 text-cyan-300" />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Cloud File Storage</p>
              <p className="font-semibold">Frontend delivery track</p>
            </div>
          </Link>

          <p className="mt-10 text-sm uppercase tracking-[0.3em] text-cyan-300">{eyebrow}</p>
          <h1 className="mt-3 text-4xl font-semibold leading-tight md:text-5xl">{title}</h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-slate-300">{description}</p>

          <div className="mt-10 grid gap-4 sm:grid-cols-2">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <p className="text-sm text-slate-300">Что уже отражено в UI</p>
              <p className="mt-3 text-lg font-medium">Роутинг, auth flow, file manager, trash, quota, security</p>
            </div>
            <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <p className="text-sm text-slate-300">Чего ждём от backend</p>
              <p className="mt-3 text-lg font-medium">Реальные endpoints Auth/File/Preview и upload pipeline</p>
            </div>
          </div>
        </div>

        <div className="rounded-[32px] border border-white/80 bg-white/85 p-6 shadow-[0_30px_90px_rgba(148,163,184,0.18)] backdrop-blur md:p-8">
          {children}
          {footer ? <div className="mt-6 text-sm text-slate-600">{footer}</div> : null}
        </div>
      </div>
    </div>
  )
}

export default AuthShell

