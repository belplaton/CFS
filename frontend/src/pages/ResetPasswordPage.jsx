import { Link, useSearchParams } from 'react-router-dom'

import { useI18n } from '@/components/app/I18nProvider'
import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

function ResetPasswordPage() {
  const { t } = useI18n()
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') ?? 'name@cloudstorage.dev'

  return (
    <AuthShell
      description={t('resetPassword.description')}
      eyebrow={t('resetPassword.eyebrow')}
      footer={
        <span>
          {t('resetPassword.backQuestion')}{' '}
          <Link className="font-medium underline underline-offset-4" to="/login">{t('resetPassword.openLogin')}</Link>
        </span>
      }
      title={t('resetPassword.title')}
    >
      <Card className="border-0 bg-transparent shadow-none">
        <CardHeader className="px-0 pt-0">
          <CardTitle className="text-3xl">{t('resetPassword.cardTitle')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-0">
          <div className="rounded-lg border bg-muted/40 p-5 text-sm leading-7 text-foreground">
            {t('resetPassword.demoEmailInfo', { email })}
          </div>
          <form className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="new-password">
                {t('resetPassword.newPassword')}
              </label>
              <Input id="new-password" name="password" placeholder={t('resetPassword.newPasswordPlaceholder')} type="password" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="repeat-password">
                {t('resetPassword.repeatPassword')}
              </label>
              <Input id="repeat-password" name="passwordRepeat" placeholder={t('resetPassword.repeatPasswordPlaceholder')} type="password" />
            </div>
            <Button asChild className="w-full py-6 text-base">
              <Link to="/login">{t('resetPassword.saveAndBack')}</Link>
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default ResetPasswordPage

