import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

function NotFoundPage() {
  return (
    <div className="surface-grid flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-xl rounded-xl border bg-card p-10 text-center shadow-sm">
        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">404</p>
        <h1 className="mt-4 text-4xl font-semibold">Страница не найдена</h1>
        <p className="mt-4 text-sm leading-7 text-muted-foreground">
          Маршрут отсутствует в текущем фронтенд-срезе. Вернитесь на главную или откройте файловый
          менеджер.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Button asChild className="px-6">
            <Link to="/">Главная</Link>
          </Button>
          <Button asChild className="px-6" variant="outline">
            <Link to="/app/files">Приложение</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}

export default NotFoundPage

