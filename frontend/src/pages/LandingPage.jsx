import {
  ArrowRight,
  Cloud,
  FolderTree,
  HardDrive,
  LockKeyhole,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
  UploadCloud,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { useI18n } from '@/components/app/I18nProvider'
import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/auth-store'

const features = [
  {
    icon: UploadCloud,
    titleKey: 'landing.pillars.workflowTitle',
    descriptionKey: 'landing.pillars.workflowDescription',
  },
  {
    icon: LockKeyhole,
    titleKey: 'landing.pillars.authTitle',
    descriptionKey: 'landing.pillars.authDescription',
  },
  {
    icon: Search,
    titleKey: 'landing.pillars.integrationTitle',
    descriptionKey: 'landing.pillars.integrationDescription',
  },
]

const scopeItems = [
  { icon: HardDrive, key: 'landing.scopeItem1' },
  { icon: ShieldCheck, key: 'landing.scopeItem2' },
  { icon: Search, key: 'landing.scopeItem3' },
]

function LandingPage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const { t } = useI18n()

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 md:px-8">
          <Link className="flex items-center gap-2.5" to="/">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border bg-muted">
              <Cloud className="h-4.5 w-4.5 text-foreground" />
            </div>
            <span className="text-base font-semibold tracking-tight">{t('appShell.brandTitle')}</span>
          </Link>

          <nav className="hidden items-center gap-1 md:flex">
            <a className="rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground" href="#features">
              {t('landing.navFeatures')}
            </a>
            <a className="rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground" href="#scope">
              {t('landing.navScope')}
            </a>
          </nav>

          <div className="flex items-center gap-2">
            <ThemeSwitcher compact />
            <Button asChild className="px-4" size="sm" variant="ghost">
              <Link to="/login">{t('landing.login')}</Link>
            </Button>
            <Button asChild className="px-4" size="sm">
              <Link to={isAuthenticated ? '/app/files' : '/register'}>
                {isAuthenticated ? t('landing.openApp') : t('landing.start')}
              </Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/5" />
        <div className="relative mx-auto max-w-6xl px-4 py-20 md:px-8 md:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border bg-muted/60 px-4 py-1.5 text-sm text-muted-foreground backdrop-blur-sm">
              <Sparkles className="h-3.5 w-3.5" />
              {t('landing.badge')}
            </div>

            <h1 className="text-4xl font-semibold leading-tight tracking-tight text-balance md:text-6xl md:leading-[1.1]">
              {t('landing.heroTitle')}
            </h1>

            <p className="mt-6 text-base leading-relaxed text-muted-foreground md:text-lg md:leading-relaxed">
              {t('landing.heroDescription')}
            </p>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              <Button asChild className="h-11 px-6 text-base" size="lg">
                <Link to={isAuthenticated ? '/app/files' : '/register'}>
                  {t('landing.openFileManager')}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild className="h-11 px-6 text-base" size="lg" variant="outline">
                <Link to="/login">
                  {t('landing.login')}
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t bg-muted/30" id="features">
        <div className="mx-auto max-w-6xl px-4 py-20 md:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{t('landing.scopeTitle')}</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight md:text-4xl">{t('landing.featuresTitle')}</h2>
          </div>

          <div className="mt-14 grid gap-6 md:grid-cols-3">
            {features.map(({ descriptionKey, icon: Icon, titleKey }) => (
              <div
                className="group rounded-xl border bg-background p-8 shadow-sm transition-shadow hover:shadow-md"
                key={titleKey}
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-xl border bg-muted transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-6 text-lg font-semibold">{t(titleKey)}</h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{t(descriptionKey)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Scope */}
      <section id="scope">
        <div className="mx-auto max-w-6xl px-4 py-20 md:px-8">
          <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{t('landing.scopeTitle')}</p>
              <h2 className="mt-4 text-3xl font-semibold tracking-tight md:text-4xl">{t('landing.scopeHeading')}</h2>
              <p className="mt-4 text-base leading-relaxed text-muted-foreground">{t('landing.scopeDescription')}</p>
            </div>

            <div className="space-y-4">
              {scopeItems.map(({ icon: Icon, key }) => (
                <div className="flex items-start gap-4 rounded-xl border bg-card p-5 shadow-sm" key={key}>
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
                    <Icon className="h-4.5 w-4.5" />
                  </div>
                  <p className="text-sm leading-relaxed text-muted-foreground pt-2">{t(key)}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t bg-muted/30">
        <div className="mx-auto max-w-6xl px-4 py-20 md:px-8">
          <div className="rounded-2xl border bg-card p-10 text-center shadow-sm md:p-16">
            <h2 className="text-3xl font-semibold tracking-tight md:text-4xl">{t('landing.ctaTitle')}</h2>
            <p className="mx-auto mt-4 max-w-xl text-base text-muted-foreground">{t('landing.ctaDescription')}</p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Button asChild className="h-11 px-6 text-base" size="lg">
                <Link to={isAuthenticated ? '/app/files' : '/register'}>
                  {isAuthenticated ? t('landing.openApp') : t('landing.start')}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-6 md:px-8">
          <div className="flex items-center gap-2">
            <Cloud className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{t('appShell.brandTitle')}</span>
          </div>
          <p className="text-xs text-muted-foreground">{t('landing.footerCopy')}</p>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
