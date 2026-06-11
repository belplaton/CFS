import { useEffect, useMemo, useState } from 'react'
import { Download, FileSpreadsheet, FileText, FileType2, X } from 'lucide-react'

import client from '@/api/client'
import { useI18n } from '@/components/app/I18nProvider'
import { Button } from '@/components/ui/button'
import { formatBytes, formatDate, getFileTypeLabel } from '@/lib/utils'

function PreviewBody({ item, previewBlobUrl, previewError, previewText, previewState, t }) {
  if (previewState === 'loading') {
    return (
      <div className="rounded-xl border bg-card p-8 text-sm text-muted-foreground">
        {t('preview.loading')}
      </div>
    )
  }

  if (previewError) {
    return (
      <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-8 text-sm leading-7 text-foreground">
        {previewError}
      </div>
    )
  }

  if (item.preview === 'image' && previewBlobUrl) {
    return (
      <div className="overflow-hidden rounded-xl border bg-card">
        <img
          alt={item.name}
          className="max-h-[520px] w-full object-contain bg-muted/30"
          src={previewBlobUrl}
        />
      </div>
    )
  }

  if (item.preview === 'pdf' && previewBlobUrl) {
    return (
      <div className="overflow-hidden rounded-xl border bg-card">
        <iframe className="h-[520px] w-full" src={previewBlobUrl} title={item.name} />
      </div>
    )
  }

  if (item.preview === 'text') {
    return (
      <div className="rounded-xl border bg-card p-6">
        <FileText className="h-10 w-10 text-foreground" />
        <pre className="mt-6 max-h-[420px] overflow-auto whitespace-pre-wrap text-sm leading-6 text-foreground">
          {previewText || t('preview.textEmpty')}
        </pre>
      </div>
    )
  }

  if (item.preview === 'document') {
    return (
      <div className="rounded-xl border bg-card p-8">
        <FileSpreadsheet className="h-10 w-10 text-foreground" />
        <p className="mt-6 text-2xl font-semibold">{t('preview.documentPlaceholder')}</p>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
          {t('preview.documentBackendStatus')}
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border bg-card p-8">
      <FileType2 className="h-10 w-10 text-muted-foreground" />
      <p className="mt-6 text-2xl font-semibold">{t('preview.metadataPlaceholder')}</p>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
        {t('preview.fallbackBackendStatus')}
      </p>
    </div>
  )
}

function PreviewModal({ item, onClose, onDownload }) {
  const { language, t } = useI18n()
  const [previewBlobUrl, setPreviewBlobUrl] = useState(null)
  const [previewText, setPreviewText] = useState('')
  const [previewState, setPreviewState] = useState('idle')
  const [previewError, setPreviewError] = useState('')

  const shouldFetchBinary = useMemo(
    () => item && ['image', 'pdf', 'text'].includes(item.preview),
    [item],
  )

  useEffect(() => {
    if (!item || !shouldFetchBinary) {
      setPreviewBlobUrl(null)
      setPreviewText('')
      setPreviewState('idle')
      setPreviewError('')
      return undefined
    }

    let isActive = true
    let objectUrl = null

    async function loadPreview() {
      setPreviewState('loading')
      setPreviewError('')

      try {
        const response = await client.get(`/files/${item.id}/download`, {
          responseType: 'blob',
        })
        if (!isActive) {
          return
        }

        const blob = response.data
        if (item.preview === 'text') {
          setPreviewText(await blob.text())
        } else {
          objectUrl = window.URL.createObjectURL(blob)
          setPreviewBlobUrl(objectUrl)
        }
        setPreviewState('ready')
      } catch (error) {
        if (!isActive) {
          return
        }

        setPreviewState('error')
        setPreviewError(
          error.response?.data?.detail
            || t('preview.errorFallback'),
        )
      }
    }

    void loadPreview()

    return () => {
      isActive = false
      if (objectUrl) {
        window.URL.revokeObjectURL(objectUrl)
      }
    }
  }, [item, shouldFetchBinary])

  if (!item) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm">
      <div className="max-h-[90vh] w-full max-w-5xl overflow-y-auto rounded-xl border bg-background shadow-2xl">
        <div className="flex items-center justify-between border-b px-6 py-5 md:px-8">
          <div className="min-w-0">
            <p className="text-sm text-muted-foreground">{getFileTypeLabel(item, t)}</p>
            <h3 className="truncate text-2xl font-semibold">{item.name}</h3>
          </div>
          <Button onClick={onClose} size="icon" variant="ghost">
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div className="grid gap-6 p-6 md:grid-cols-[1.4fr_0.8fr] md:p-8">
          <PreviewBody
            item={item}
            previewBlobUrl={previewBlobUrl}
            previewError={previewError}
            previewState={previewState}
            previewText={previewText}
            t={t}
          />

          <div className="space-y-4">
            <div className="rounded-xl border bg-card p-6">
              <p className="text-sm text-muted-foreground">{t('preview.metadata')}</p>
              <dl className="mt-5 space-y-4 text-sm">
                <div className="flex items-center justify-between gap-4">
                  <dt>{t('preview.type')}</dt>
                  <dd>{getFileTypeLabel(item, t)}</dd>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <dt>{t('preview.size')}</dt>
                  <dd>{item.size ? formatBytes(item.size) : t('common.none')}</dd>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <dt>{t('preview.updated')}</dt>
                  <dd>{formatDate(item.updatedAt, language)}</dd>
                </div>
              </dl>
            </div>

            <div className="rounded-xl border bg-card p-6">
              <p className="text-sm text-muted-foreground">{t('preview.sourceTitle')}</p>
              <p className="mt-4 text-sm leading-7 text-muted-foreground">
                {t('preview.sourceDescription')}
              </p>
            </div>

            <Button className="w-full gap-2" onClick={() => onDownload(item)} variant="outline">
              <Download className="h-4 w-4" />
              {t('preview.downloadFile')}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PreviewModal
