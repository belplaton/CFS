import { Link, useNavigate } from 'react-router-dom'

import { useI18n } from '@/components/app/I18nProvider'
import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

function ForgotPasswordPage() {
  const { t } = useI18n()
  const navigate = useNavigate()

  return (
    <AuthShell
      description={t('forgotPassword.description')}
      eyebrow={t('forgotPassword.eyebrow')}
      footer={
        <span>
          {t('forgotPassword.remembered')}{' '}
          <Link className="font-medium underline underline-offset-4" to="/login">{t('forgotPassword.backToLogin')}</Link>
        </span>
      }
      title={t('forgotPassword.title')}
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">{t('forgotPassword.cardTitle')}</CardTitle>
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
                {t('common.email')}
              </label>
              <Input id="forgot-email" name="email" placeholder="name@cloudstorage.dev" type="email" />
            </div>
            <Button className="w-full py-6 text-base" type="submit">
              {t('forgotPassword.submit')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default ForgotPasswordPage

