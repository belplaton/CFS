import { HardDrive } from 'lucide-react'

import { formatBytes } from '@/lib/utils'

function QuotaCard({ usedBytes, quotaBytes, plan }) {
  const progress = Math.min(Math.round((usedBytes / quotaBytes) * 100), 100)
  const remainingBytes = Math.max(quotaBytes - usedBytes, 0)

  return (
    <div className="rounded-xl border bg-background p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Storage quota</p>
          <h2 className="mt-3 text-2xl font-semibold">{plan} plan</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {formatBytes(usedBytes)} из {formatBytes(quotaBytes)}
          </p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border bg-muted">
          <HardDrive className="h-5 w-5 text-foreground" />
        </div>
      </div>

      <div className="mt-6 rounded-xl border bg-muted/40 p-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Текущая загрузка</span>
          <span className="font-medium">{progress}%</span>
        </div>

        <div className="mt-4 h-2 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-[width]"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
          <span>Свободно</span>
          <span>{formatBytes(remainingBytes)}</span>
        </div>
      </div>
    </div>
  )
}

export default QuotaCard

