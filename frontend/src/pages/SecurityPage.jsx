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

  return (
    <div className="space-y-6">
      <section className="rounded-[32px] border border-slate-200 bg-white p-6 shadow-[0_15px_40px_rgba(148,163,184,0.12)] md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-emerald-700">Security</p>
            <h1 className="mt-3 text-3xl font-semibold">Безопасность аккаунта</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
              Этот раздел закрывает фронтенд-часть для email verification, password recovery и
              2FA-настроек. Реальное TOTP-подключение появится после backend endpoints.
            </p>
          </div>
          <div className="rounded-[28px] border border-emerald-100 bg-emerald-50 px-5 py-4 text-sm text-emerald-950">
            {user?.emailVerified ? 'Email подтверждён' : 'Email ещё не подтверждён'}
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="rounded-[32px] border border-slate-200 bg-slate-950 p-6 text-white shadow-[0_20px_60px_rgba(15,23,42,0.22)] md:p-8">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10">
            <ShieldCheck className="h-6 w-6 text-cyan-300" />
          </div>
          <h2 className="mt-6 text-3xl font-semibold">Two-factor access</h2>
          <p className="mt-4 text-sm leading-7 text-slate-300">
            Пока это безопасный UI stub для будущей интеграции: на backend будут QR-код, TOTP
            challenge при логине и backup codes.
          </p>
          <div className="mt-8 rounded-[28px] border border-white/10 bg-white/5 p-5">
            <p className="text-sm text-slate-300">Текущее состояние</p>
            <p className="mt-2 text-2xl font-semibold">
              {user?.twoFactorEnabled ? '2FA включена' : '2FA выключена'}
            </p>
          </div>
          <Button className="mt-6 w-full rounded-full py-6 text-base" onClick={toggleTwoFactor}>
            {user?.twoFactorEnabled ? 'Отключить 2FA' : 'Включить 2FA'}
          </Button>
        </div>

        <div className="grid gap-4">
          {tracks.map(({ description, icon: Icon, title }) => (
            <div
              className="rounded-[32px] border border-slate-200 bg-white p-6 shadow-[0_15px_40px_rgba(148,163,184,0.12)]"
              key={title}
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white">
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="mt-5 text-2xl font-semibold">{title}</h3>
              <p className="mt-3 text-sm leading-7 text-slate-600">{description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default SecurityPage

