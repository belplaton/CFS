import { useState } from 'react'
import { Navigate, Link, useLocation, useNavigate } from 'react-router-dom'

import { useI18n } from '@/components/app/I18nProvider'
import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/store/auth-store'

function LoginPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const location = useLocation()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const pendingTwoFactor = useAuthStore((state) => state.pendingTwoFactor)
  const login = useAuthStore((state) => state.login)
  const loginWithGoogle = useAuthStore((state) => state.loginWithGoogle)
  const verifyTwoFactor = useAuthStore((state) => state.verifyTwoFactor)
  const cancelTwoFactor = useAuthStore((state) => state.cancelTwoFactor)
  const [twoFactorError, setTwoFactorError] = useState('')

  if (isAuthenticated) {
    return <Navigate replace to="/app/files" />
  }

  const from = location.state?.from?.pathname ?? '/app/files'

  return (
    <AuthShell
      description={t('login.description')}
      eyebrow={t('login.eyebrow')}
      footer={
        <span>
          {t('login.noAccount')}{' '}
          <Link className="font-medium underline underline-offset-4" to="/register">{t('login.create')}</Link>
        </span>
      }
      title={t('login.title')}
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">
            {pendingTwoFactor ? t('login.cardTitleTwoFactor') : t('login.cardTitleSignIn')}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          {pendingTwoFactor ? (
            <>
              <div className="rounded-lg border bg-muted/40 p-5 text-sm leading-7 text-foreground">
                {t('login.twoFactorIntro', { email: pendingTwoFactor.email })}
              </div>

              <form
                className="space-y-4"
                onSubmit={(event) => {
                  event.preventDefault()
                  const formData = new FormData(event.currentTarget)
                  const result = verifyTwoFactor({
                    code: formData.get('totpCode')?.toString().trim() ?? '',
                  })

                  if (!result.success) {
                    setTwoFactorError(t('login.totpInvalid'))
                    return
                  }

                  setTwoFactorError('')
                  navigate(from, { replace: true })
                }}
              >
                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="login-totp">
                    {t('login.totpLabel')}
                  </label>
                  <Input autoFocus id="login-totp" inputMode="numeric" name="totpCode" placeholder={t('login.totpPlaceholder')} />
                </div>

                {twoFactorError ? (
                  <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    {twoFactorError}
                  </div>
                ) : null}

                <Button className="w-full py-6 text-base" type="submit">
                  {t('login.confirmLogin')}
                </Button>
              </form>

              <Button
                className="w-full py-6 text-base"
                onClick={() => {
                  setTwoFactorError('')
                  cancelTwoFactor()
                }}
                variant="outline"
              >
                {t('login.backToLogin')}
              </Button>
            </>
          ) : (
            <>
              <form
                className="space-y-4"
                onSubmit={(event) => {
                  event.preventDefault()
                  const formData = new FormData(event.currentTarget)
                  login({
                    email: formData.get('email')?.toString().trim() ?? '',
                  })

                  if (useAuthStore.getState().isAuthenticated) {
                    navigate(from, { replace: true })
                  }
                }}
              >
                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="login-email">
                    Email
                  </label>
                  <Input defaultValue="demo@cloudstorage.dev" id="login-email" name="email" type="email" />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-4">
                    <label className="text-sm font-medium" htmlFor="login-password">
                      {t('common.password')}
                    </label>
                    <Link className="text-sm underline underline-offset-4" to="/forgot-password">
                      {t('login.forgotPassword')}
                    </Link>
                  </div>
                  <Input defaultValue="demo-password" id="login-password" name="password" type="password" />
                </div>
                <Button className="mt-2 w-full py-6 text-base" type="submit">
                  {t('login.signIn')}
                </Button>
              </form>

              <Button
                className="w-full py-6 text-base"
                onClick={() => {
                  loginWithGoogle()

                  if (useAuthStore.getState().isAuthenticated) {
                    navigate(from, { replace: true })
                  }
                }}
                variant="outline"
              >
                {t('login.continueGoogle')}
              </Button>

              <div className="rounded-lg border bg-muted/40 p-5 text-sm leading-7 text-foreground">
                {t('login.demoHint')}
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default LoginPage

