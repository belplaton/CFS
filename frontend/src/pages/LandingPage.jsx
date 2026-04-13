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

import { useI18n } from '@/components/app/I18nProvider'
import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/auth-store'

function LandingPage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const { t } = useI18n()

  const pillars = [
    {
      icon: UploadCloud,
      title: t('landing.pillars.workflowTitle'),
      description: t('landing.pillars.workflowDescription'),
    },
    {
      icon: LockKeyhole,
      title: t('landing.pillars.authTitle'),
      description: t('landing.pillars.authDescription'),
    },
    {
      icon: Search,
      title: t('landing.pillars.integrationTitle'),
      description: t('landing.pillars.integrationDescription'),
    },
  ]

  return (
    <div className="surface-grid min-h-screen bg-background px-4 py-6 text-foreground md:px-8">
      <div className="mx-auto max-w-6xl">
        <header className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card px-6 py-5 shadow-sm">
          <div>
            <p className="text-xs text-muted-foreground">{t('appShell.brandTitle')}</p>
            <h1 className="mt-2 text-2xl font-semibold md:text-3xl">{t('landing.workspaceTitle')}</h1>
          </div>
          <div className="flex flex-wrap gap-3">
            <ThemeSwitcher compact />
            <Button asChild className="px-5" variant="ghost">
              <Link to="/login">{t('landing.login')}</Link>
            </Button>
            <Button asChild className="px-5">
              <Link to={isAuthenticated ? '/app/files' : '/register'}>
                {isAuthenticated ? t('landing.openApp') : t('landing.start')}
              </Link>
            </Button>
          </div>
        </header>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-xl border bg-card p-8 shadow-sm md:p-12">
            <div className="inline-flex items-center gap-2 rounded-md border bg-muted px-3 py-1.5 text-sm text-muted-foreground">
              <Sparkles className="h-4 w-4" />
              {t('landing.badge')}
            </div>

            <h2 className="mt-8 max-w-4xl text-4xl font-semibold leading-tight text-balance md:text-6xl">
              {t('landing.heroTitle')}
            </h2>

            <p className="mt-6 max-w-2xl text-base leading-8 text-muted-foreground md:text-lg">
              {t('landing.heroDescription')}
            </p>

            <div className="mt-10 flex flex-wrap gap-3">
              <Button asChild className="px-6 py-6 text-base">
                <Link to={isAuthenticated ? '/app/files' : '/login'}>
                  {t('landing.openFileManager')}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild className="px-6 py-6 text-base" variant="outline">
                <Link to="/app/security">{t('landing.openSecurityFlow')}</Link>
              </Button>
            </div>
          </div>

          <div className="grid gap-6">
            <div className="rounded-xl border bg-card p-8 shadow-sm">
              <p className="text-xs text-muted-foreground">{t('landing.scopeTitle')}</p>
              <ul className="mt-6 space-y-4 text-sm leading-7 text-muted-foreground">
                <li className="flex gap-3">
                  <FolderTree className="mt-1 h-4 w-4 shrink-0 text-foreground" />
                  {t('landing.scopeItem1')}
                </li>
                <li className="flex gap-3">
                  <ShieldCheck className="mt-1 h-4 w-4 shrink-0 text-foreground" />
                  {t('landing.scopeItem2')}
                </li>
                <li className="flex gap-3">
                  <Search className="mt-1 h-4 w-4 shrink-0 text-foreground" />
                  {t('landing.scopeItem3')}
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

