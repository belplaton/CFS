import { Link, useSearchParams } from 'react-router-dom'

import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') ?? 'name@cloudstorage.dev'

  return (
    <AuthShell
      description="Новый пароль пока не уходит в backend, но отдельная форма и маршрут уже собраны под полный reset-password flow."
      eyebrow="New Password"
      footer={
        <span>
          Вернуться ко входу? <Link className="font-medium text-sky-700" to="/login">Открыть login</Link>
        </span>
      }
      title="Установка нового пароля"
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">Reset password</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <div className="rounded-[28px] border border-amber-100 bg-amber-50 p-5 text-sm leading-7 text-amber-950">
            В демо-режиме письмо имитируется переходом на эту страницу для <strong>{email}</strong>.
          </div>
          <form className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="new-password">
                Новый пароль
              </label>
              <Input id="new-password" name="password" placeholder="Минимум 8 символов" type="password" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="repeat-password">
                Повторите пароль
              </label>
              <Input id="repeat-password" name="passwordRepeat" placeholder="Повторите новый пароль" type="password" />
            </div>
            <Button asChild className="w-full rounded-full py-6 text-base">
              <Link to="/login">Сохранить и вернуться ко входу</Link>
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default ResetPasswordPage

