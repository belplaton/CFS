import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Eye, EyeOff, KeyRound, MailCheck, ShieldCheck, Smartphone } from 'lucide-react'

import { useI18n } from '@/components/app/I18nProvider'
import LanguageSwitcher from '@/components/app/LanguageSwitcher'
import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/store/auth-store'

function SecurityPage() {
  const { t } = useI18n()
  const { toggleTwoFactor, user } = useAuthStore((state) => ({
    toggleTwoFactor: state.toggleTwoFactor,
    user: state.user,
  }))
  const backupCodes = user?.backupCodes ?? []
  const [isBackupAuthModalOpen, setIsBackupAuthModalOpen] = useState(false)
  const [isBackupCodesModalOpen, setIsBackupCodesModalOpen] = useState(false)
  const [backupPassword, setBackupPassword] = useState('')
  const [backupPasswordError, setBackupPasswordError] = useState('')

  const submitBackupAuth = (event) => {
    event.preventDefault()
    if (backupPassword.trim().length < 6) {
      setBackupPasswordError(t('security.identityError'))
      return
    }

    setBackupPasswordError('')
    setIsBackupCodesModalOpen(true)
    setIsBackupAuthModalOpen(false)
    setBackupPassword('')
  }

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

      <section className="grid items-stretch gap-3 lg:grid-cols-3 [grid-auto-rows:1fr]">
        <article className="flex h-full min-h-[200px] flex-col gap-2 rounded-xl border bg-card p-3.5 shadow-sm">
          <div className="flex h-10 w-10 min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
            <ShieldCheck className="h-5 w-5 text-foreground" />
          </div>
          <h2 className="text-lg font-semibold">{t('security.twoFactorTitle')}</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            {t('security.twoFactorDescription')}
          </p>
          <div className="rounded-lg border bg-muted/30 px-3 py-2 text-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="text-muted-foreground">{t('security.status')}</span>
              <span className="font-semibold">{user?.twoFactorEnabled ? t('security.enabled') : t('security.disabled')}</span>
            </div>
            {user?.twoFactorEnabled ? (
              <div className="mt-1.5 flex items-center justify-between gap-2">
                <span className="text-muted-foreground">{t('security.demoCode')}</span>
                <strong className="text-foreground">246810</strong>
              </div>
            ) : null}
          </div>
          <Button className="mt-auto h-10 w-full text-base" onClick={toggleTwoFactor}>
            {user?.twoFactorEnabled ? t('security.disable2fa') : t('security.enable2fa')}
          </Button>
        </article>

        <article className="flex h-full min-h-[200px] flex-col gap-2 rounded-xl border bg-card p-3.5 shadow-sm">
          <div className="flex h-10 w-10 min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
            <MailCheck className="h-5 w-5" />
          </div>
          <h2 className="text-lg font-semibold">{t('security.emailTitle')}</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            {t('security.emailDescription')}
          </p>
          <div className="mt-auto grid grid-cols-2 gap-2">
            <Button asChild className="h-10 w-full px-3 text-base" size="sm">
              <Link to="/verify-email">{t('security.openVerify')}</Link>
            </Button>
            <Button asChild className="h-10 w-full px-3 text-base" size="sm" variant="outline">
              <Link to="/register">{t('security.resendFlow')}</Link>
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

        <article className="flex h-full min-h-[200px] flex-col gap-2 rounded-xl border bg-card p-3.5 shadow-sm">
          <div className="flex h-10 w-10 min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
            <Smartphone className="h-5 w-5" />
          </div>
          <h2 className="text-lg font-semibold">{t('security.backupTitle')}</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            {t('security.backupDescription')}
          </p>

          {!user?.twoFactorEnabled ? (
            <div className="rounded-md border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
              {t('security.backupUnavailable')}
            </div>
          ) : null}

          {user?.twoFactorEnabled ? (
            <Button
              className="mt-auto h-10 w-full text-base"
              onClick={() => {
                setIsBackupAuthModalOpen(true)
                setBackupPasswordError('')
              }}
              variant="outline"
            >
              <Eye className="mr-2 h-4 w-4" />
              {t('security.showBackupCodes')}
            </Button>
          ) : null}
        </article>
      </section>

      {isBackupAuthModalOpen ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border bg-background p-5 shadow-2xl">
            <h3 className="text-xl font-semibold">{t('security.identityTitle')}</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {t('security.identityDescription')}
            </p>

            <form className="mt-4 space-y-3" onSubmit={submitBackupAuth}>
              <Input
                className="h-10"
                onChange={(event) => setBackupPassword(event.target.value)}
                placeholder={t('security.identityPlaceholder')}
                type="password"
                value={backupPassword}
              />
              {backupPasswordError ? (
                <p className="text-xs text-red-300">{backupPasswordError}</p>
              ) : null}
              <div className="flex gap-2">
                <Button className="h-10 flex-1" type="submit">
                  {t('security.confirm')}
                </Button>
                <Button
                  className="h-10 flex-1"
                  onClick={() => {
                    setIsBackupAuthModalOpen(false)
                    setBackupPassword('')
                    setBackupPasswordError('')
                  }}
                  type="button"
                  variant="outline"
                >
                  {t('common.cancel')}
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {isBackupCodesModalOpen ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-xl border bg-background p-5 shadow-2xl">
            <h3 className="text-xl font-semibold">{t('security.backupModalTitle')}</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {t('security.backupModalDescription')}
            </p>

            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              {backupCodes.length > 0 ? backupCodes.map((code) => (
                <div className="rounded-md border bg-muted/30 px-3 py-2 text-sm font-medium" key={code}>
                  {code}
                </div>
              )) : (
                <div className="rounded-md border bg-muted/30 px-3 py-2 text-sm text-muted-foreground sm:col-span-2">
                  {t('security.backupMissing')}
                </div>
              )}
            </div>

            <div className="mt-4 flex justify-end">
              <Button
                className="h-10"
                onClick={() => setIsBackupCodesModalOpen(false)}
                variant="outline"
              >
                <EyeOff className="mr-2 h-4 w-4" />
                {t('security.hideBackupCodes')}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default SecurityPage

