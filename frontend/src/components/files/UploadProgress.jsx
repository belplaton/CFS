import { useEffect, useState } from 'react'
import { CheckCircle2, XCircle, RefreshCw, X, Upload } from 'lucide-react'

import { useI18n } from '@/components/app/I18nProvider'
import { Button } from '@/components/ui/button'
import { useFileStore } from '@/store/file-store'
import { formatBytes } from '@/lib/utils'

function UploadProgress() {
  const { t } = useI18n()
  const uploadQueue = useFileStore((s) => s.uploadQueue)
  const cancelUpload = useFileStore((s) => s.cancelUpload)
  const retryUpload = useFileStore((s) => s.retryUpload)
  const removeCompletedUploads = useFileStore((s) => s.removeCompletedUploads)
  const [isExpanded, setIsExpanded] = useState(false)

  if (!uploadQueue.length) {
    return null
  }

  const activeCount = uploadQueue.filter((e) => e.status === 'uploading').length
  const queuedCount = uploadQueue.filter((e) => e.status === 'queued').length
  const doneCount = uploadQueue.filter((e) => e.status === 'done').length
  const errorCount = uploadQueue.filter((e) => e.status === 'error').length

  const totalProgress = uploadQueue.length
    ? Math.round(uploadQueue.reduce((sum, e) => sum + e.progress, 0) / uploadQueue.length)
    : 0

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80 overflow-hidden rounded-xl border bg-background shadow-2xl">
      <button
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium hover:bg-muted/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
        type="button"
      >
        <span className="flex items-center gap-2">
          <Upload className="h-4 w-4" />
          {activeCount > 0
            ? t('uploadProgress.uploading', { count: activeCount })
            : queuedCount > 0
              ? t('uploadProgress.queued', { count: queuedCount })
              : t('uploadProgress.complete')}
        </span>
        <span className="text-xs text-muted-foreground">
          {doneCount}/{uploadQueue.length}
        </span>
      </button>

      <div className="h-1 w-full bg-muted">
        <div
          className="h-full bg-primary transition-[width] duration-300"
          style={{ width: `${totalProgress}%` }}
        />
      </div>

      {isExpanded && (
        <div className="max-h-60 overflow-y-auto">
          {uploadQueue.map((entry) => (
            <div
              className="flex items-center gap-3 border-t border-border/50 px-4 py-2.5"
              key={entry.id}
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium">{entry.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatBytes(entry.size)}
                </p>
                {entry.status === 'uploading' && (
                  <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-[width] duration-300"
                      style={{ width: `${entry.progress}%` }}
                    />
                  </div>
                )}
                {entry.status === 'error' && (
                  <p className="mt-1 text-xs text-destructive">{entry.error}</p>
                )}
              </div>
              <div className="shrink-0">
                {entry.status === 'uploading' && (
                  <Button
                    onClick={() => cancelUpload(entry.id)}
                    size="icon"
                    variant="ghost"
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                )}
                {entry.status === 'error' && (
                  <Button
                    onClick={() => retryUpload(entry.id)}
                    size="icon"
                    variant="ghost"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                  </Button>
                )}
                {entry.status === 'done' && (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                )}
                {entry.status === 'queued' && (
                  <span className="text-xs text-muted-foreground">{t('uploadProgress.waiting')}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {doneCount + errorCount === uploadQueue.length && doneCount + errorCount > 0 && (
        <div className="border-t border-border/50 px-4 py-2">
          <Button
            className="w-full text-xs"
            onClick={removeCompletedUploads}
            size="sm"
            variant="ghost"
          >
            {t('uploadProgress.clear')}
          </Button>
        </div>
      )}
    </div>
  )
}

export default UploadProgress
