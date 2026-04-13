import { Download, FileSpreadsheet, FileText, FileType2, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { formatBytes, formatDate, getFileTypeLabel } from '@/lib/utils'

function PreviewArtwork({ item }) {
  if (item.preview === 'image') {
    return (
      <div className="flex min-h-[320px] items-end rounded-xl border bg-muted p-6">
        <div>
          <p className="text-sm text-muted-foreground">Image Preview</p>
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
          <p className="mt-6 text-2xl font-semibold">PDF viewer slot</p>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
            Подготовлено место под браузерный просмотр PDF. После готовности Preview Service
            сюда подключается поток с рендерами страниц или iframe на presigned URL.
          </p>
        </div>
      </div>
    )
  }

  if (item.preview === 'document') {
    return (
      <div className="rounded-xl border bg-card p-8">
        <FileSpreadsheet className="h-10 w-10 text-foreground" />
        <p className="mt-6 text-2xl font-semibold">Document preview placeholder</p>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
          Компонент готов к отображению docx/xlsx preview и thumbnails. До появления preview API
          показывает описание точки интеграции.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border bg-card p-8">
      <FileType2 className="h-10 w-10 text-muted-foreground" />
      <p className="mt-6 text-2xl font-semibold">Metadata preview</p>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
        Для нестандартных форматов сейчас доступен безопасный fallback с метаданными. Дальше сюда
        можно добавить presigned download или специализированный viewer.
      </p>
    </div>
  )
}

function PreviewModal({ item, onClose }) {
  if (!item) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm">
      <div className="max-h-[90vh] w-full max-w-5xl overflow-y-auto rounded-xl border bg-background shadow-2xl">
        <div className="flex items-center justify-between border-b px-6 py-5 md:px-8">
          <div className="min-w-0">
            <p className="text-sm text-muted-foreground">{getFileTypeLabel(item)}</p>
            <h3 className="truncate text-2xl font-semibold">{item.name}</h3>
          </div>
          <Button onClick={onClose} size="icon" variant="ghost">
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div className="grid gap-6 p-6 md:grid-cols-[1.4fr_0.8fr] md:p-8">
          <PreviewArtwork item={item} />

          <div className="space-y-4">
            <div className="rounded-xl border bg-card p-6">
              <p className="text-sm text-muted-foreground">Метаданные</p>
              <dl className="mt-5 space-y-4 text-sm">
                <div className="flex items-center justify-between gap-4">
                  <dt>Тип</dt>
                  <dd>{getFileTypeLabel(item)}</dd>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <dt>Размер</dt>
                  <dd>{item.size ? formatBytes(item.size) : 'n/a'}</dd>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <dt>Обновлён</dt>
                  <dd>{formatDate(item.updatedAt)}</dd>
                </div>
              </dl>
            </div>

            <div className="rounded-xl border bg-card p-6">
              <p className="text-sm text-muted-foreground">Следующий backend шаг</p>
              <p className="mt-4 text-sm leading-7 text-muted-foreground">
                Подключить `GET /api/preview/:id` и `GET /api/files/:id/download`, чтобы modal
                перестал быть демо-слоем и стал полноценным viewer.
              </p>
            </div>

            <Button className="w-full gap-2" variant="outline">
              <Download className="h-4 w-4" />
              Скачать файл
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PreviewModal

