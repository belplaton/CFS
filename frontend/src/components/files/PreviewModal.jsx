import { Download, FileImage, FileSpreadsheet, FileText, FileType2, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { formatBytes, formatDate, getFileTypeLabel } from '@/lib/utils'

function PreviewArtwork({ item }) {
  if (item.preview === 'image') {
    return (
      <div className={`flex min-h-[320px] items-end rounded-[28px] bg-gradient-to-br ${item.accent} p-6 text-white`}>
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-white/70">Image Preview</p>
          <p className="mt-3 text-3xl font-semibold">{item.name}</p>
        </div>
      </div>
    )
  }

  if (item.preview === 'pdf') {
    return (
      <div className="rounded-[28px] border border-slate-200 bg-white p-6">
        <div className="rounded-[24px] bg-slate-100 p-8">
          <FileText className="h-10 w-10 text-rose-500" />
          <p className="mt-6 text-2xl font-semibold">PDF viewer slot</p>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
            Подготовлено место под браузерный просмотр PDF. После готовности Preview Service
            сюда подключается поток с рендерами страниц или iframe на presigned URL.
          </p>
        </div>
      </div>
    )
  }

  if (item.preview === 'document') {
    return (
      <div className="rounded-[28px] border border-slate-200 bg-white p-8">
        <FileSpreadsheet className="h-10 w-10 text-emerald-500" />
        <p className="mt-6 text-2xl font-semibold">Document preview placeholder</p>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
          Компонент готов к отображению docx/xlsx preview и thumbnails. До появления preview API
          показывает описание точки интеграции.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-[28px] border border-slate-200 bg-white p-8">
      <FileType2 className="h-10 w-10 text-slate-500" />
      <p className="mt-6 text-2xl font-semibold">Metadata preview</p>
      <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
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
      <div className="max-h-[90vh] w-full max-w-5xl overflow-y-auto rounded-[32px] border border-white/10 bg-[#f8fafc] shadow-[0_30px_100px_rgba(15,23,42,0.45)]">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5 md:px-8">
          <div className="min-w-0">
            <p className="text-sm uppercase tracking-[0.3em] text-sky-700">{getFileTypeLabel(item)}</p>
            <h3 className="truncate text-2xl font-semibold">{item.name}</h3>
          </div>
          <Button className="rounded-full" onClick={onClose} size="icon" variant="ghost">
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div className="grid gap-6 p-6 md:grid-cols-[1.4fr_0.8fr] md:p-8">
          <PreviewArtwork item={item} />

          <div className="space-y-4">
            <div className="rounded-[28px] border border-slate-200 bg-white p-6">
              <p className="text-sm uppercase tracking-[0.3em] text-slate-500">Метаданные</p>
              <dl className="mt-5 space-y-4 text-sm text-slate-700">
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

            <div className="rounded-[28px] border border-slate-200 bg-white p-6">
              <p className="text-sm uppercase tracking-[0.3em] text-slate-500">Следующий backend шаг</p>
              <p className="mt-4 text-sm leading-7 text-slate-600">
                Подключить `GET /api/preview/:id` и `GET /api/files/:id/download`, чтобы modal
                перестал быть демо-слоем и стал полноценным viewer.
              </p>
            </div>

            <Button className="w-full gap-2 rounded-full" variant="outline">
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

