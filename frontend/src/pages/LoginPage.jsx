import { useState } from 'react'
import { Navigate, Link, useLocation, useNavigate } from 'react-router-dom'

import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/store/auth-store'

function LoginPage() {
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
      description="Текущий backend auth ещё не реализован полностью, поэтому экран уже построен как production-like форма, но работает через локальный store до подключения API."
      eyebrow="Login"
      footer={
        <span>
          Нет аккаунта? <Link className="font-medium underline underline-offset-4" to="/register">Создать</Link>
        </span>
      }
      title="Вход в рабочее пространство"
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">{pendingTwoFactor ? 'Two-factor check' : 'Sign in'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          {pendingTwoFactor ? (
            <>
              <div className="rounded-lg border bg-muted/40 p-5 text-sm leading-7 text-foreground">
                Для аккаунта <strong>{pendingTwoFactor.email}</strong> включена двухфакторная защита.
                В демо-режиме используй TOTP-код <strong>246810</strong> или один из backup codes из
                раздела безопасности.
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
                    setTwoFactorError('Неверный TOTP или backup code. Попробуй ещё раз.')
                    return
                  }

                  setTwoFactorError('')
                  navigate(from, { replace: true })
                }}
              >
                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="login-totp">
                    Код подтверждения
                  </label>
                  <Input autoFocus id="login-totp" inputMode="numeric" name="totpCode" placeholder="246810 или backup code" />
                </div>

                {twoFactorError ? (
                  <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    {twoFactorError}
                  </div>
                ) : null}

                <Button className="w-full py-6 text-base" type="submit">
                  Подтвердить вход
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
                Вернуться к логину
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
                      Пароль
                    </label>
                    <Link className="text-sm underline underline-offset-4" to="/forgot-password">
                      Забыли пароль?
                    </Link>
                  </div>
                  <Input defaultValue="demo-password" id="login-password" name="password" type="password" />
                </div>
                <Button className="mt-2 w-full py-6 text-base" type="submit">
                  Войти
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
                Продолжить через Google
              </Button>

              <div className="rounded-lg border bg-muted/40 p-5 text-sm leading-7 text-foreground">
                Демо-режим: если для аккаунта включена 2FA, после логина откроется отдельный шаг
                подтверждения. Дальше сюда подключается `POST /api/auth/login` и TOTP challenge flow.
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default LoginPage

