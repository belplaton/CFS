import { Link } from 'react-router-dom'
import { KeyRound, MailCheck } from 'lucide-react'
import { useState } from 'react'

import { useI18n } from '@/components/app/I18nProvider'
import LanguageSwitcher from '@/components/app/LanguageSwitcher'
import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/auth-store'

function SecurityPage() {
  const { t } = useI18n()
  const user = useAuthStore((state) => state.user)
  const requestEmailVerification = useAuthStore((state) => state.requestEmailVerification)
  const [statusMessage, setStatusMessage] = useState('')
  const displayName = user?.full_name?.trim() || t('security.defaultUserName')
  const displayEmail = user?.email?.trim() || t('security.noEmail')

  return (
    <div className="space-y-4">
      <section className="rounded-xl border bg-card p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{t('security.eyebrow')}</p>
            <h1 className="mt-2 text-3xl font-semibold">{t('security.title')}</h1>
            <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
              {t('security.description')}
            </p>
            <div className="mt-4 rounded-lg border bg-muted/30 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{t('security.signedInAs')}</p>
              <p className="mt-1 text-sm font-semibold text-foreground">{displayName}</p>
              <p className="text-sm text-muted-foreground">{displayEmail}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="rounded-md border bg-muted px-4 py-2 text-sm">
              {user?.emailVerified ? t('security.emailVerified') : t('security.emailNotVerified')}
            </div>
            <LanguageSwitcher compact />
            <ThemeSwitcher compact />
          </div>
        </div>
      </section>

      <section className="grid items-stretch gap-3 lg:grid-cols-2 [grid-auto-rows:1fr]">
        <article className="flex h-full min-h-[200px] flex-col gap-2 rounded-xl border bg-card p-3.5 shadow-sm">
          <div className="flex h-10 w-10 min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
            <MailCheck className="h-5 w-5" />
          </div>
          <h2 className="text-lg font-semibold">{t('security.emailTitle')}</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            {t('security.emailDescription')}
          </p>
          <div className="mt-auto grid grid-cols-2 gap-2">
            <Button
              className="h-10 w-full px-3 text-base"
              disabled={user?.emailVerified}
              onClick={async () => {
                const result = await requestEmailVerification()
                if (result.success) {
                  setStatusMessage(result.message || t('security.verifyRequested'))
                  if (result.actionUrl) {
                    window.location.assign(result.actionUrl)
                  }
                } else {
                  setStatusMessage(result.error || t('security.verifyFailed'))
                }
              }}
              size="sm"
            >
              {t('security.openVerify')}
            </Button>
            <Button
              className="h-10 w-full px-3 text-base"
              disabled={user?.emailVerified}
              onClick={async () => {
                const result = await requestEmailVerification()
                setStatusMessage(
                  result.success
                    ? (result.message || t('security.verifyRequested'))
                    : (result.error || t('security.verifyFailed')),
                )
              }}
              size="sm"
              variant="outline"
            >
              {t('security.resendFlow')}
            </Button>
          </div>
        </article>

        <article className="flex h-full min-h-[200px] flex-col gap-2 rounded-xl border bg-card p-3.5 shadow-sm">
          <div className="flex h-10 w-10 min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
            <KeyRound className="h-5 w-5" />
          </div>
          <h2 className="text-lg font-semibold">{t('security.passwordTitle')}</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            {t('security.passwordDescription')}
          </p>
          <div className="mt-auto grid grid-cols-2 gap-2">
            <Button asChild className="h-10 w-full px-3 text-base" size="sm">
              <Link to="/forgot-password">{t('security.requestReset')}</Link>
            </Button>
            <Button asChild className="h-10 w-full px-3 text-base" size="sm" variant="outline">
              <Link to="/reset-password">{t('security.newPassword')}</Link>
            </Button>
          </div>
        </article>
      </section>
      {statusMessage ? (
        <div className="rounded-lg border bg-muted/40 px-4 py-3 text-sm text-foreground">
          {statusMessage}
        </div>
      ) : null}
    </div>
  )
}

export default SecurityPage

