import { Link, useNavigate } from 'react-router-dom'

import client from '@/api/client'
import { useI18n } from '@/components/app/I18nProvider'
import AuthShell from '@/components/auth/AuthShell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useState } from 'react'

function ForgotPasswordPage() {
  const { t } = useI18n()
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(false)
  const [statusMessage, setStatusMessage] = useState('')
  const [statusType, setStatusType] = useState('info')

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
            onSubmit={async (event) => {
              event.preventDefault()
              const formData = new FormData(event.currentTarget)
              const email = formData.get('email')?.toString().trim() ?? ''

              setIsLoading(true)
              setStatusMessage('')
              setStatusType('info')
              try {
                const response = await client.post('/auth/forgot-password', { email })
                setStatusMessage(response.data?.message || 'If email exists, password reset instructions will be sent')
                setStatusType('success')
                const actionUrl = response.data?.action_url
                if (actionUrl) {
                  window.location.assign(actionUrl)
                } else {
                  navigate(`/reset-password?email=${encodeURIComponent(email)}`)
                }
              } catch (error) {
                setStatusMessage(error.response?.data?.detail || 'Unable to start password reset flow')
                setStatusType('error')
              } finally {
                setIsLoading(false)
              }
            }}
          >
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="forgot-email">
                {t('common.email')}
              </label>
              <Input id="forgot-email" name="email" placeholder="name@cloudstorage.dev" type="email" />
            </div>
            {statusMessage ? (
              <div className={`rounded-lg p-4 text-sm ${
                statusType === 'error'
                  ? 'border border-destructive/30 bg-destructive/10 text-destructive'
                  : 'border border-emerald-500/30 bg-emerald-500/10 text-foreground'
              }`}>
                {statusMessage}
              </div>
            ) : null}
            <Button className="w-full py-6 text-base" disabled={isLoading} type="submit">
              {isLoading ? t('common.loading') : t('forgotPassword.submit')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </AuthShell>
  )
}

export default ForgotPasswordPage

