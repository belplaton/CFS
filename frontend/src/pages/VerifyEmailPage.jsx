import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'

import { useI18n } from '@/components/app/I18nProvider'
import AuthShell from '@/components/auth/AuthShell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuthStore } from '@/store/auth-store'

function VerifyEmailPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') ?? 'name@cloudstorage.dev'
  const token = searchParams.get('token') ?? ''
  const verifyEmailToken = useAuthStore((state) => state.verifyEmailToken)
  const clearError = useAuthStore((state) => state.clearError)
  const isLoading = useAuthStore((state) => state.isLoading)
  const error = useAuthStore((state) => state.error)
  const [statusMessage, setStatusMessage] = useState(token ? t('verifyEmail.verifying') : '')
  const hasRequested = useRef(false)

  useEffect(() => {
    clearError()
  }, [clearError])

  useEffect(() => {
    if (!token || hasRequested.current) {
      return
    }
    hasRequested.current = true

    void (async () => {
      const result = await verifyEmailToken(token)
      if (result.success) {
        setStatusMessage(t('verifyEmail.success'))
        window.setTimeout(() => {
          navigate('/login', {
            replace: true,
            state: { notice: t('verifyEmail.loginNotice') },
          })
        }, 1200)
      } else {
        setStatusMessage('')
      }
    })()
  }, [navigate, token, verifyEmailToken, t])

  return (
    <AuthShell
      description={t('verifyEmail.description')}
      eyebrow={t('verifyEmail.eyebrow')}
      footer={
        <span>
          {t('verifyEmail.alreadyVerified')}{' '}
          <Link className="font-medium underline underline-offset-4" to="/login">{t('verifyEmail.goToLogin')}</Link>
        </span>
      }
      title={t('verifyEmail.title')}
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">{t('verifyEmail.cardTitle')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <div className="rounded-lg border bg-muted/40 p-5 text-sm leading-7 text-foreground">
            {t('verifyEmail.sentTo', { email })}
          </div>
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
          {!token && !isLoading ? (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-5 text-sm leading-7 text-foreground">
              {t('verifyEmail.missingToken')}
            </div>
          ) : null}
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default VerifyEmailPage

