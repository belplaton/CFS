import { HardDrive } from 'lucide-react'

import { formatBytes } from '@/lib/utils'

function QuotaCard({ usedBytes, quotaBytes, plan }) {
  const progress = Math.min(Math.round((usedBytes / quotaBytes) * 100), 100)

  return (
    <div className="rounded-[28px] border border-slate-200 bg-slate-950 p-6 text-white shadow-[0_20px_60px_rgba(15,23,42,0.18)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">Quota</p>
          <h2 className="mt-3 text-2xl font-semibold">{plan} plan</h2>
          <p className="mt-2 text-sm text-slate-300">
            {formatBytes(usedBytes)} из {formatBytes(quotaBytes)}
          </p>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10">
          <HardDrive className="h-5 w-5 text-cyan-300" />
        </div>
      </div>

      <div className="mt-6 h-3 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-[linear-gradient(90deg,_#22d3ee,_#f59e0b)] transition-[width]"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="mt-4 flex items-center justify-between text-sm text-slate-300">
        <span>Текущая загрузка</span>
        <span>{progress}%</span>
      </div>
    </div>
  )
}

export default QuotaCard

