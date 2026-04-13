import { Link } from 'react-router-dom'

import { useI18n } from '@/components/app/I18nProvider'
import { Button } from '@/components/ui/button'

function NotFoundPage() {
  const { t } = useI18n()

  return (
    <div className="surface-grid flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-xl rounded-xl border bg-card p-10 text-center shadow-sm">
        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">404</p>
        <h1 className="mt-4 text-4xl font-semibold">{t('notFound.title')}</h1>
        <p className="mt-4 text-sm leading-7 text-muted-foreground">
          {t('notFound.description')}
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Button asChild className="px-6">
            <Link to="/">{t('notFound.home')}</Link>
          </Button>
          <Button asChild className="px-6" variant="outline">
            <Link to="/app/files">{t('notFound.app')}</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}

export default NotFoundPage

