import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { useI18n } from '@/components/app/I18nProvider'
import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/store/auth-store'

function ResetPasswordPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') ?? 'name@cloudstorage.dev'
  const token = searchParams.get('token') ?? ''
  const resetPassword = useAuthStore((state) => state.resetPassword)
  const clearError = useAuthStore((state) => state.clearError)
  const isLoading = useAuthStore((state) => state.isLoading)
  const error = useAuthStore((state) => state.error)
  const [statusMessage, setStatusMessage] = useState('')
  const canSubmit = Boolean(token)

  useEffect(() => {
    clearError()
  }, [clearError])

  return (
    <AuthShell
      description={t('resetPassword.description')}
      eyebrow={t('resetPassword.eyebrow')}
      footer={
        <span>
          {t('resetPassword.backQuestion')}{' '}
          <Link className="font-medium underline underline-offset-4" to="/login">{t('resetPassword.openLogin')}</Link>
        </span>
      }
      title={t('resetPassword.title')}
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">{t('resetPassword.cardTitle')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <div className="rounded-lg border bg-muted/40 p-5 text-sm leading-7 text-foreground">
            {t('resetPassword.demoEmailInfo', { email })}
          </div>
          {!canSubmit ? (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-5 text-sm leading-7 text-foreground">
              {t('resetPassword.backendStatus')}
            </div>
          ) : null}
          {statusMessage ? (
            <div className="rounded-lg border bg-muted/40 p-5 text-sm leading-7 text-foreground">
              {statusMessage}
            </div>
          ) : null}
          {error ? (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-5 text-sm leading-7 text-destructive">
              {error}
            </div>
          ) : null}
          <form
            className={`space-y-4 ${canSubmit ? '' : 'opacity-60'}`}
            onSubmit={async (event) => {
              event.preventDefault()
              if (!canSubmit) {
                return
              }

              const formData = new FormData(event.currentTarget)
              const password = formData.get('password')?.toString() ?? ''
              const passwordRepeat = formData.get('passwordRepeat')?.toString() ?? ''

              if (!password || password !== passwordRepeat) {
                setStatusMessage(t('resetPassword.passwordMismatch'))
                return
              }

              const result = await resetPassword({ token, password })
              if (result.success) {
                navigate('/login', {
                  replace: true,
                  state: { notice: t('resetPassword.success') },
                })
              }
            }}
          >
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="new-password">
                {t('resetPassword.newPassword')}
              </label>
              <Input disabled={!canSubmit || isLoading} id="new-password" name="password" placeholder={t('resetPassword.newPasswordPlaceholder')} type="password" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="repeat-password">
                {t('resetPassword.repeatPassword')}
              </label>
              <Input disabled={!canSubmit || isLoading} id="repeat-password" name="passwordRepeat" placeholder={t('resetPassword.repeatPasswordPlaceholder')} type="password" />
            </div>
            <Button className="w-full py-6 text-base" disabled={!canSubmit || isLoading} type="submit">
              {isLoading ? t('common.loading') : t('resetPassword.saveAndBack')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default ResetPasswordPage

