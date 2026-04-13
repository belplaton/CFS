import { Link, useNavigate } from 'react-router-dom'

import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

function ForgotPasswordPage() {
  const navigate = useNavigate()

  return (
    <AuthShell
      description="Страница подготовлена под request-reset endpoint и уже вписана в auth-flow приложения."
      eyebrow="Password Reset"
      footer={
        <span>
          Вспомнили пароль? <Link className="font-medium underline underline-offset-4" to="/login">Назад ко входу</Link>
        </span>
      }
      title="Запрос на сброс пароля"
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">Reset access</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault()
              const formData = new FormData(event.currentTarget)
              const email = formData.get('email')?.toString().trim() ?? ''
              navigate(`/reset-password?email=${encodeURIComponent(email)}`)
            }}
          >
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="forgot-email">
                Email
              </label>
              <Input id="forgot-email" name="email" placeholder="name@cloudstorage.dev" type="email" />
            </div>
            <Button className="w-full py-6 text-base" type="submit">
              Отправить ссылку
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default ForgotPasswordPage

