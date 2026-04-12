import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[linear-gradient(180deg,_#f7fbff,_#f8f2e8)] px-4">
      <div className="max-w-xl rounded-[32px] border border-white/80 bg-white/85 p-10 text-center shadow-[0_20px_60px_rgba(148,163,184,0.18)]">
        <p className="text-xs uppercase tracking-[0.35em] text-sky-700">404</p>
        <h1 className="mt-4 text-4xl font-semibold">Страница не найдена</h1>
        <p className="mt-4 text-sm leading-7 text-slate-600">
          Маршрут отсутствует в текущем фронтенд-срезе. Вернитесь на главную или откройте файловый
          менеджер.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Button asChild className="rounded-full px-6">
            <Link to="/">Главная</Link>
          </Button>
          <Button asChild className="rounded-full px-6" variant="outline">
            <Link to="/app/files">Приложение</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}

export default NotFoundPage

