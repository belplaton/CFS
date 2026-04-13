import { Link, useNavigate } from 'react-router-dom'

import { useI18n } from '@/components/app/I18nProvider'
import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/store/auth-store'

function RegisterPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const register = useAuthStore((state) => state.register)

  return (
    <AuthShell
      description={t('register.description')}
      eyebrow={t('register.eyebrow')}
      footer={
        <span>
          {t('register.haveAccount')}{' '}
          <Link className="font-medium underline underline-offset-4" to="/login">{t('register.signIn')}</Link>
        </span>
      }
      title={t('register.title')}
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">{t('register.cardTitle')}</CardTitle>
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
                {t('register.name')}
              </label>
              <Input id="register-name" name="fullName" placeholder={t('register.namePlaceholder')} type="text" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="register-email">
                {t('common.email')}
              </label>
              <Input id="register-email" name="email" placeholder="name@cloudstorage.dev" type="email" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="register-password">
                {t('common.password')}
              </label>
              <Input id="register-password" name="password" placeholder={t('register.passwordPlaceholder')} type="password" />
            </div>
            <Button className="w-full py-6 text-base" type="submit">
              {t('register.submit')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default RegisterPage

