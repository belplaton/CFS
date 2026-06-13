import { Check, Crown, Sparkles } from 'lucide-react'

import { useI18n } from '@/components/app/I18nProvider'
import LanguageSwitcher from '@/components/app/LanguageSwitcher'
import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import { Button } from '@/components/ui/button'
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
  const switchPlan = useAuthStore((state) => state.switchPlan)
  const isLoading = useAuthStore((state) => state.isLoading)
  const quota = useFileStore((state) => state.quota)
  const refreshQuota = useFileStore((state) => state.refreshQuota)
  const usedBytes = quota.used
  const currentPlan = (user?.plan ?? 'Free').toLowerCase()

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
            <Button onClick={() => refreshQuota()} size="sm" variant="outline">
              {t('billing.refreshQuota')}
            </Button>
            <LanguageSwitcher compact />
            <ThemeSwitcher compact />
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        {plans.map((plan) => {
          const isCurrent = currentPlan === plan.id
          const isDowngradeBlocked = usedBytes > plan.quotaBytes
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
                  variant={isCurrent || isDowngradeBlocked ? 'outline' : 'default'}
                  disabled={isCurrent || isDowngradeBlocked || isLoading}
                  onClick={async () => {
                    await switchPlan(plan.id)
                  }}
                >
                  {isCurrent ? t('billing.currentPlan') : isLoading ? t('common.loading') : t('billing.choosePlan')}
                </Button>
              </div>
            </article>
          )
        })}
      </div>
    </div>
  )
}

export default BillingPage
