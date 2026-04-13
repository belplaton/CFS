import { KeyRound, MailCheck, ShieldCheck, Smartphone } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/store/auth-store'

const tracks = [
  {
    title: 'Email verification',
    description: 'UI уже разведён по отдельным маршрутам и ожидает реальные verify/resend endpoints.',
    icon: MailCheck,
  },
  {
    title: 'Password recovery',
    description: 'Экран запроса письма и экран нового пароля готовы под auth-flow из roadmap.',
    icon: KeyRound,
  },
  {
    title: '2FA / TOTP',
    description: 'Настройки безопасности подготовлены под QR-код, challenge step и backup codes.',
    icon: Smartphone,
  },
]

function SecurityPage() {
  const { toggleTwoFactor, user } = useAuthStore((state) => ({
    toggleTwoFactor: state.toggleTwoFactor,
    user: state.user,
  }))
  const backupCodes = user?.backupCodes ?? []
  const totpSecret = user?.totpSecret ?? 'JBSW-Y3DP-EHPK-3PXP'

  return (
    <div className="space-y-6">
      <section className="rounded-xl border bg-card p-6 shadow-sm md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Security</p>
            <h1 className="mt-3 text-3xl font-semibold">Безопасность аккаунта</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground">
              Этот раздел закрывает фронтенд-часть для email verification, password recovery и
              2FA-настроек. Реальное TOTP-подключение появится после backend endpoints.
            </p>
          </div>
          <div className="rounded-md border bg-muted px-4 py-2 text-sm">
            {user?.emailVerified ? 'Email подтверждён' : 'Email ещё не подтверждён'}
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="rounded-xl border bg-card p-6 shadow-sm md:p-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg border bg-muted">
            <ShieldCheck className="h-5 w-5 text-foreground" />
          </div>
          <h2 className="mt-6 text-3xl font-semibold">Two-factor access</h2>
          <p className="mt-4 text-sm leading-7 text-muted-foreground">
            Сейчас это mock-flow без backend: после включения 2FA следующий логин уже требует
            отдельный TOTP challenge step. Позже сюда подключатся QR-код, реальная генерация кодов
            и серверная валидация.
          </p>
          <div className="mt-8 rounded-xl border bg-muted/40 p-5">
            <p className="text-sm text-muted-foreground">Текущее состояние</p>
            <p className="mt-2 text-2xl font-semibold">
              {user?.twoFactorEnabled ? '2FA включена' : '2FA выключена'}
            </p>
            {user?.twoFactorEnabled ? (
              <div className="mt-4 space-y-4">
                <div>
                  <p className="text-sm font-medium">Демо TOTP-код</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Для mock challenge используется код <strong>246810</strong>.
                  </p>
                </div>

                <div>
                  <p className="text-sm font-medium">Mock secret</p>
                  <p className="mt-2 text-sm text-muted-foreground">{totpSecret}</p>
                </div>

                <div>
                  <p className="text-sm font-medium">Backup codes</p>
                  <div className="mt-3 grid gap-2 sm:grid-cols-2">
                    {backupCodes.length > 0 ? backupCodes.map((code) => (
                      <div className="rounded-md border bg-background px-3 py-2 text-sm" key={code}>
                        {code}
                      </div>
                    )) : (
                      <div className="rounded-md border bg-background px-3 py-2 text-sm text-muted-foreground sm:col-span-2">
                        Backup codes будут показаны после повторного включения 2FA.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
          <Button className="mt-6 w-full py-6 text-base" onClick={toggleTwoFactor}>
            {user?.twoFactorEnabled ? 'Отключить 2FA' : 'Включить 2FA'}
          </Button>
        </div>

        <div className="grid gap-4">
          {tracks.map(({ description, icon: Icon, title }) => (
            <div
              className="rounded-xl border bg-card p-6 shadow-sm"
              key={title}
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border bg-muted">
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="mt-5 text-2xl font-semibold">{title}</h3>
              <p className="mt-3 text-sm leading-7 text-muted-foreground">{description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default SecurityPage

