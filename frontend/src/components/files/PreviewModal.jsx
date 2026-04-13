import { Download, FileSpreadsheet, FileText, FileType2, X } from 'lucide-react'

import { useI18n } from '@/components/app/I18nProvider'
import { Button } from '@/components/ui/button'
import { formatBytes, formatDate, getFileTypeLabel } from '@/lib/utils'

function PreviewArtwork({ item, t }) {
  if (item.preview === 'image') {
    return (
      <div className="flex min-h-[320px] items-end rounded-xl border bg-muted p-6">
        <div>
          <p className="text-sm text-muted-foreground">{t('preview.imagePreview')}</p>
          <p className="mt-3 text-3xl font-semibold">{item.name}</p>
        </div>
      </div>
    )
  }

  if (item.preview === 'pdf') {
    return (
      <div className="rounded-xl border bg-card p-6">
        <div className="rounded-lg border bg-muted p-8">
          <FileText className="h-10 w-10 text-foreground" />
          <p className="mt-6 text-2xl font-semibold">{t('preview.pdfSlot')}</p>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
            {t('preview.pdfDescription')}
          </p>
        </div>
      </div>
    )
  }

  if (item.preview === 'document') {
    return (
      <div className="rounded-xl border bg-card p-8">
        <FileSpreadsheet className="h-10 w-10 text-foreground" />
        <p className="mt-6 text-2xl font-semibold">{t('preview.documentPlaceholder')}</p>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
          {t('preview.documentDescription')}
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border bg-card p-8">
      <FileType2 className="h-10 w-10 text-muted-foreground" />
      <p className="mt-6 text-2xl font-semibold">{t('preview.metadataPlaceholder')}</p>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
        {t('preview.metadataDescription')}
      </p>
    </div>
  )
}

function PreviewModal({ item, onClose }) {
  const { language, t } = useI18n()

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
          <PreviewArtwork item={item} t={t} />

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
              <p className="text-sm text-muted-foreground">{t('preview.backendStep')}</p>
              <p className="mt-4 text-sm leading-7 text-muted-foreground">
                {t('preview.backendStepDescription')}
              </p>
            </div>

            <Button className="w-full gap-2" variant="outline">
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

