import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Eye, EyeOff, KeyRound, MailCheck, ShieldCheck, Smartphone } from 'lucide-react'

import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/store/auth-store'

function SecurityPage() {
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
      setBackupPasswordError('Введите пароль (минимум 6 символов).')
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
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Security</p>
            <h1 className="mt-2 text-3xl font-semibold">Безопасность аккаунта</h1>
            <p className="mt-2 max-w-3xl text-sm text-muted-foreground">
              Центр управления методами входа, восстановления и 2FA. Все экраны готовы для
              интеграции backend endpoints.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="rounded-md border bg-muted px-4 py-2 text-sm">
              {user?.emailVerified ? 'Email подтверждён' : 'Email ещё не подтверждён'}
            </div>
            <ThemeSwitcher compact settingsMode />
          </div>
        </div>
      </section>

      <section className="grid items-stretch gap-3 lg:grid-cols-3 [grid-auto-rows:1fr]">
        <article className="flex h-full min-h-[200px] flex-col gap-2 rounded-xl border bg-card p-3.5 shadow-sm">
          <div className="flex h-10 w-10 min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
            <ShieldCheck className="h-5 w-5 text-foreground" />
          </div>
          <h2 className="text-lg font-semibold">Two-factor access</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            После включения вход требует отдельный TOTP challenge step.
          </p>
          <div className="rounded-lg border bg-muted/30 px-3 py-2 text-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="text-muted-foreground">Статус</span>
              <span className="font-semibold">{user?.twoFactorEnabled ? 'Включена' : 'Выключена'}</span>
            </div>
            {user?.twoFactorEnabled ? (
              <div className="mt-1.5 flex items-center justify-between gap-2">
                <span className="text-muted-foreground">Демо-код</span>
                <strong className="text-foreground">246810</strong>
              </div>
            ) : null}
          </div>
          <Button className="mt-auto h-10 w-full text-base" onClick={toggleTwoFactor}>
            {user?.twoFactorEnabled ? 'Отключить 2FA' : 'Включить 2FA'}
          </Button>
        </article>

        <article className="flex h-full min-h-[200px] flex-col gap-2 rounded-xl border bg-card p-3.5 shadow-sm">
          <div className="flex h-10 w-10 min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
            <MailCheck className="h-5 w-5" />
          </div>
          <h2 className="text-lg font-semibold">Email verification</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            Проверка email и повторная отправка ссылки подтверждения.
          </p>
          <div className="mt-auto grid grid-cols-2 gap-2">
            <Button asChild className="h-10 w-full px-3 text-base" size="sm">
              <Link to="/verify-email">Открыть verify</Link>
            </Button>
            <Button asChild className="h-10 w-full px-3 text-base" size="sm" variant="outline">
              <Link to="/register">Resend flow</Link>
            </Button>
          </div>
        </article>

        <article className="flex h-full min-h-[200px] flex-col gap-2 rounded-xl border bg-card p-3.5 shadow-sm">
          <div className="flex h-10 w-10 min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
            <KeyRound className="h-5 w-5" />
          </div>
          <h2 className="text-lg font-semibold">Password recovery</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            Запрос письма для reset и экран ввода нового пароля.
          </p>
          <div className="mt-auto grid grid-cols-2 gap-2">
            <Button asChild className="h-10 w-full px-3 text-base" size="sm">
              <Link to="/forgot-password">Запросить reset</Link>
            </Button>
            <Button asChild className="h-10 w-full px-3 text-base" size="sm" variant="outline">
              <Link to="/reset-password">Новый пароль</Link>
            </Button>
          </div>
        </article>

        <article className="flex h-full min-h-[200px] flex-col gap-2 rounded-xl border bg-card p-3.5 shadow-sm">
          <div className="flex h-10 w-10 min-h-10 min-w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
            <Smartphone className="h-5 w-5" />
          </div>
          <h2 className="text-lg font-semibold">Backup codes</h2>
          <p className="text-sm leading-6 text-muted-foreground">
            Коды скрыты по умолчанию. Для показа требуется повторный ввод пароля.
          </p>

          {!user?.twoFactorEnabled ? (
            <div className="rounded-md border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
              Backup codes доступны после включения 2FA.
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
              Показать backup codes
            </Button>
          ) : null}
        </article>
      </section>

      {isBackupAuthModalOpen ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border bg-background p-5 shadow-2xl">
            <h3 className="text-xl font-semibold">Подтверждение личности</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Для показа backup codes повторно введите пароль от аккаунта.
            </p>

            <form className="mt-4 space-y-3" onSubmit={submitBackupAuth}>
              <Input
                className="h-10"
                onChange={(event) => setBackupPassword(event.target.value)}
                placeholder="Повторно введите пароль"
                type="password"
                value={backupPassword}
              />
              {backupPasswordError ? (
                <p className="text-xs text-red-300">{backupPasswordError}</p>
              ) : null}
              <div className="flex gap-2">
                <Button className="h-10 flex-1" type="submit">
                  Подтвердить
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
                  Отмена
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {isBackupCodesModalOpen ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-xl border bg-background p-5 shadow-2xl">
            <h3 className="text-xl font-semibold">Backup codes</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Сохраните коды в безопасном месте. Каждый код можно использовать только один раз.
            </p>

            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              {backupCodes.length > 0 ? backupCodes.map((code) => (
                <div className="rounded-md border bg-muted/30 px-3 py-2 text-sm font-medium" key={code}>
                  {code}
                </div>
              )) : (
                <div className="rounded-md border bg-muted/30 px-3 py-2 text-sm text-muted-foreground sm:col-span-2">
                  Backup codes отсутствуют. Выключите и снова включите 2FA для генерации.
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
                Скрыть backup codes
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default SecurityPage

