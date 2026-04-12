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
  const login = useAuthStore((state) => state.login)
  const loginWithGoogle = useAuthStore((state) => state.loginWithGoogle)

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
          Нет аккаунта? <Link className="font-medium text-sky-700" to="/register">Создать</Link>
        </span>
      }
      title="Вход в рабочее пространство"
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">Sign in</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault()
              const formData = new FormData(event.currentTarget)
              login({
                email: formData.get('email')?.toString().trim() ?? '',
              })
              navigate(from, { replace: true })
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
                <Link className="text-sm text-sky-700" to="/forgot-password">
                  Забыли пароль?
                </Link>
              </div>
              <Input defaultValue="demo-password" id="login-password" name="password" type="password" />
            </div>
            <Button className="mt-2 w-full rounded-full py-6 text-base" type="submit">
              Войти
            </Button>
          </form>

          <Button
            className="w-full rounded-full py-6 text-base"
            onClick={() => {
              loginWithGoogle()
              navigate(from, { replace: true })
            }}
            variant="outline"
          >
            Продолжить через Google
          </Button>

          <div className="rounded-[28px] border border-sky-100 bg-sky-50 p-5 text-sm leading-7 text-sky-950">
            Демо-режим: форма сразу открывает SPA после входа. Дальше сюда подключается
            `POST /api/auth/login` и refresh token flow.
          </div>
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default LoginPage

