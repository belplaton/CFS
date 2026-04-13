import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuthStore } from '@/store/auth-store'

function VerifyEmailPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const verifyEmail = useAuthStore((state) => state.verifyEmail)
  const pendingEmail = useAuthStore((state) => state.pendingEmail)
  const email = searchParams.get('email') ?? pendingEmail ?? 'name@cloudstorage.dev'

  return (
    <AuthShell
      description="Страница верификации уже выделена в отдельный маршрут и готова под verify-email endpoint, повторную отправку письма и состояние успешной активации."
      eyebrow="Email Verification"
      footer={
        <span>
          Уже подтвердили почту? <Link className="font-medium underline underline-offset-4" to="/login">Перейти ко входу</Link>
        </span>
      }
      title="Подтверждение email"
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">Verify account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <div className="rounded-lg border bg-muted/40 p-5 text-sm leading-7 text-foreground">
            Проверочное письмо направлено на <strong>{email}</strong>. В демо-режиме подтверждение
            имитируется кнопкой ниже.
          </div>
          <Button
            className="w-full py-6 text-base"
            onClick={() => {
              verifyEmail()
              navigate('/login')
            }}
          >
            Подтвердить email
          </Button>
          <Button className="w-full py-6 text-base" variant="outline">
            Отправить письмо повторно
          </Button>
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default VerifyEmailPage

