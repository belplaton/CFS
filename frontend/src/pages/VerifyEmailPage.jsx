import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { useI18n } from '@/components/app/I18nProvider'
import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuthStore } from '@/store/auth-store'

function VerifyEmailPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const verifyEmail = useAuthStore((state) => state.verifyEmail)
  const pendingEmail = useAuthStore((state) => state.pendingEmail)
  const email = searchParams.get('email') ?? pendingEmail ?? 'name@cloudstorage.dev'

  return (
    <AuthShell
      description={t('verifyEmail.description')}
      eyebrow={t('verifyEmail.eyebrow')}
      footer={
        <span>
          {t('verifyEmail.alreadyVerified')}{' '}
          <Link className="font-medium underline underline-offset-4" to="/login">{t('verifyEmail.goToLogin')}</Link>
        </span>
      }
      title={t('verifyEmail.title')}
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">{t('verifyEmail.cardTitle')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <div className="rounded-lg border bg-muted/40 p-5 text-sm leading-7 text-foreground">
            {t('verifyEmail.sentTo', { email })}
          </div>
          <Button
            className="w-full py-6 text-base"
            onClick={() => {
              verifyEmail()
              navigate('/login')
            }}
          >
            {t('verifyEmail.confirm')}
          </Button>
          <Button className="w-full py-6 text-base" variant="outline">
            {t('verifyEmail.resend')}
          </Button>
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default VerifyEmailPage

