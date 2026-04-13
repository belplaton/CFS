import { Link, useNavigate } from 'react-router-dom'

import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/store/auth-store'

function RegisterPage() {
  const navigate = useNavigate()
  const register = useAuthStore((state) => state.register)

  return (
    <AuthShell
      description="Экран регистрации уже соответствует roadmap: есть отдельная страница, подготовленная под verify-email и будущую backend-валидацию."
      eyebrow="Register"
      footer={
        <span>
          Уже есть аккаунт? <Link className="font-medium underline underline-offset-4" to="/login">Войти</Link>
        </span>
      }
      title="Создание аккаунта"
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">Create account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault()
              const formData = new FormData(event.currentTarget)
              const email = formData.get('email')?.toString().trim() ?? ''

              register({
                fullName: formData.get('fullName')?.toString().trim() ?? '',
                email,
              })

              navigate(`/verify-email?email=${encodeURIComponent(email)}`)
            }}
          >
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="register-name">
                Имя
              </label>
              <Input id="register-name" name="fullName" placeholder="Platon Belyakov" type="text" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="register-email">
                Email
              </label>
              <Input id="register-email" name="email" placeholder="name@cloudstorage.dev" type="email" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="register-password">
                Пароль
              </label>
              <Input id="register-password" name="password" placeholder="Минимум 8 символов" type="password" />
            </div>
            <Button className="w-full py-6 text-base" type="submit">
              Зарегистрироваться
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default RegisterPage

