import { useEffect, useRef, useState } from 'react'
import { Check, Crown, Sparkles } from 'lucide-react'

import { useI18n } from '@/components/app/I18nProvider'
import LanguageSwitcher from '@/components/app/LanguageSwitcher'
import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import { Button } from '@/components/ui/button'
import { getFileStats } from '@/lib/file-metrics'
import { formatBytes } from '@/lib/utils'
import { useAuthStore } from '@/store/auth-store'
import { useFileStore } from '@/store/file-store'

const plans = [
  {
    id: 'free',
    title: 'Free',
    monthly: '$0',
    quotaBytes: 5 * 1024 * 1024 * 1024,
    badgeKey: 'billing.badges.free',
    features: ['billing.features.free1', 'billing.features.free2', 'billing.features.free3'],
  },
  {
    id: 'pro',
    title: 'Pro',
    monthly: '$4.99',
    quotaBytes: 100 * 1024 * 1024 * 1024,
    badgeKey: 'billing.badges.pro',
    highlighted: true,
    features: ['billing.features.pro1', 'billing.features.pro2', 'billing.features.pro3'],
  },
  {
    id: 'team',
    title: 'Team',
    monthly: '$14.99',
    quotaBytes: 500 * 1024 * 1024 * 1024,
    badgeKey: 'billing.badges.team',
    features: ['billing.features.team1', 'billing.features.team2', 'billing.features.team3'],
  },
]

function BillingPage() {
  const { t } = useI18n()
  const user = useAuthStore((state) => state.user)
  const setStoragePlan = useAuthStore((state) => state.setStoragePlan)
  const items = useFileStore((state) => state.items)
  const usedBytes = getFileStats(items).usedBytes
  const currentPlan = (user?.plan ?? 'Free').toLowerCase()
  const [confirmPlanId, setConfirmPlanId] = useState(null)
  const [pendingPlanId, setPendingPlanId] = useState(null)
  const [status, setStatus] = useState(null)
  const timerRef = useRef(null)

  const confirmPlan = plans.find((plan) => plan.id === confirmPlanId) ?? null

  const applyPlanChange = (planId) => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    setPendingPlanId(planId)
    setStatus(null)
    timerRef.current = setTimeout(() => {
      setStoragePlan({ plan: planId })
      setPendingPlanId(null)
      setConfirmPlanId(null)
      setStatus({
        type: 'success',
        message: t('billing.successMessage'),
      })
    }, 750)
  }

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
    }
  }, [])

  return (
    <div className="space-y-5">
      <div className="rounded-xl border bg-card p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{t('billing.eyebrow')}</p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight">{t('billing.title')}</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {t('billing.description')}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {t('billing.usedNow', { used: formatBytes(usedBytes) })}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <LanguageSwitcher compact />
            <ThemeSwitcher compact />
          </div>
        </div>
      </div>

      {status?.type === 'success' ? (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">
          {status.message}
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-3">
        {plans.map((plan) => {
          const isCurrent = currentPlan === plan.id
          const isDowngradeBlocked = usedBytes > plan.quotaBytes
          const isPending = pendingPlanId === plan.id
          return (
            <article
              className={`rounded-xl border p-5 ${
                plan.highlighted ? 'border-primary bg-primary/5 shadow-sm' : 'bg-card'
              }`}
              key={plan.id}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{t(plan.badgeKey)}</p>
                  <h2 className="mt-2 text-2xl font-semibold">{plan.title}</h2>
                </div>
                {plan.highlighted ? <Sparkles className="h-5 w-5 text-primary" /> : <Crown className="h-5 w-5 text-muted-foreground" />}
              </div>

              <p className="mt-4 text-3xl font-semibold">
                {plan.monthly}
                <span className="ml-1 text-sm font-normal text-muted-foreground">{t('billing.month')}</span>
              </p>
              <p className="mt-1 text-sm text-muted-foreground">{t('billing.quota', { quota: formatBytes(plan.quotaBytes) })}</p>
              {isDowngradeBlocked ? (
                <p className="mt-1 text-xs text-amber-300">
                  {t('billing.downgradeBlocked', { used: formatBytes(usedBytes), limit: formatBytes(plan.quotaBytes) })}
                </p>
              ) : null}

              <ul className="mt-4 space-y-2">
                {plan.features.map((featureKey) => (
                  <li className="flex items-center gap-2 text-sm text-foreground" key={featureKey}>
                    <Check className="h-4 w-4 text-primary" />
                    {t(featureKey)}
                  </li>
                ))}
              </ul>

              <div className="mt-5">
                <Button
                  className="w-full"
                  onClick={() => {
                    if (isCurrent || isPending || isDowngradeBlocked) {
                      return
                    }

                    setConfirmPlanId(plan.id)
                  }}
                  variant={isCurrent || isDowngradeBlocked ? 'outline' : 'default'}
                  disabled={isDowngradeBlocked || !!pendingPlanId}
                >
                  {isCurrent ? t('billing.currentPlan') : isPending ? t('billing.applying') : t('billing.choosePlan')}
                </Button>
              </div>
            </article>
          )
        })}
      </div>

      {confirmPlan ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border bg-background p-5 shadow-2xl">
            <h3 className="text-xl font-semibold">{t('billing.confirmTitle')}</h3>
            <p className="mt-3 text-sm text-muted-foreground">
              {t('billing.confirmText', { from: user?.plan ?? 'Free', to: confirmPlan.title })}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {t('billing.confirmQuota', { quota: formatBytes(confirmPlan.quotaBytes), used: formatBytes(usedBytes) })}
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <Button onClick={() => setConfirmPlanId(null)} variant="ghost">
                {t('common.cancel')}
              </Button>
              <Button
                onClick={() => applyPlanChange(confirmPlan.id)}
                disabled={pendingPlanId === confirmPlan.id}
              >
                {pendingPlanId === confirmPlan.id ? t('billing.applying') : t('billing.confirmButton')}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default BillingPage
