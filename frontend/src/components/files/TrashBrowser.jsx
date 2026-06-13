import { RotateCcw, Trash2, FileIcon, FileSpreadsheet, FileText, Folder, Image as ImageIcon } from 'lucide-react'

import { useI18n } from '@/components/app/I18nProvider'
import { Button } from '@/components/ui/button'
import { ROOT_FOLDER_ID } from '@/lib/files-constants'
import { formatBytes, formatDate, getFileTypeLabel } from '@/lib/utils'

function getItemIcon(item) {
  if (item.kind === 'folder') {
    return <Folder className="h-5 w-5 text-foreground" />
  }

  if (item.mimeType?.startsWith('image/')) {
    return <ImageIcon className="h-5 w-5 text-foreground" />
  }

  if (item.mimeType === 'application/pdf') {
    return <FileText className="h-5 w-5 text-foreground" />
  }

  if (item.mimeType?.includes('sheet') || item.mimeType?.includes('excel')) {
    return <FileSpreadsheet className="h-5 w-5 text-foreground" />
  }

  return <FileIcon className="h-5 w-5 text-muted-foreground" />
}

function buildBreadcrumbs(foldersById, currentFolderId, t) {
  if (currentFolderId === ROOT_FOLDER_ID) {
    return [{ id: ROOT_FOLDER_ID, name: t('files.myFiles') }]
  }

  const breadcrumb = []
  let pointer = foldersById[currentFolderId]

  while (pointer) {
    breadcrumb.unshift({ id: pointer.id, name: pointer.name })
    pointer = pointer.parentId ? foldersById[pointer.parentId] : null
  }

  return [{ id: ROOT_FOLDER_ID, name: t('files.myFiles') }, ...breadcrumb]
}

function TrashBrowser({ currentFolderId, items, onDelete, onGoToFolder, onRestore }) {
  const { language, t } = useI18n()
  const foldersById = Object.fromEntries(items.filter((item) => item.kind === 'folder').map((item) => [item.id, item]))
  const breadcrumbs = buildBreadcrumbs(foldersById, currentFolderId, t)
  const visibleItems = items.filter((item) => {
    const effectiveParent = (item.parentId && foldersById[item.parentId])
      ? item.parentId
      : ROOT_FOLDER_ID
    return effectiveParent === currentFolderId
  })

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {breadcrumbs.map((crumb, index) => (
          <button
            className="inline-flex items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            key={crumb.id}
            onClick={() => onGoToFolder(crumb.id)}
            type="button"
          >
            {crumb.name}
            {index < breadcrumbs.length - 1 ? <span className="text-slate-300">/</span> : null}
          </button>
        ))}
      </div>

      {visibleItems.length === 0 ? (
        <div className="rounded-xl border border-dashed bg-muted/20 px-6 py-16 text-center">
          <p className="text-2xl font-semibold">{t('files.emptyTitle')}</p>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            {t('files.emptyDescription')}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border bg-background">
          <div className="max-h-[74vh] overflow-auto">
            <div className="min-w-[980px]">
              <div className="sticky top-0 z-20 grid h-14 grid-cols-[minmax(0,2.8fr)_160px_190px_120px_120px_96px] items-center gap-4 border-b bg-background/95 px-4 backdrop-blur">
                <span className="text-xs uppercase leading-none tracking-[0.18em] text-muted-foreground">{t('files.columns.name')}</span>
                <span className="text-xs uppercase leading-none tracking-[0.18em] text-muted-foreground">{t('files.columns.owner')}</span>
                <span className="text-xs uppercase leading-none tracking-[0.18em] text-muted-foreground">{t('trash.columns.deleted')}</span>
                <span className="text-xs uppercase leading-none tracking-[0.18em] text-muted-foreground">{t('files.columns.size')}</span>
                <span className="text-xs uppercase leading-none tracking-[0.18em] text-muted-foreground">{t('trash.columns.type')}</span>
                <span className="text-right text-xs uppercase leading-none tracking-[0.18em] text-muted-foreground">{t('files.columns.actions')}</span>
              </div>

              {visibleItems.map((item) => (
                <div
                  className="grid grid-cols-[minmax(0,2.8fr)_160px_190px_120px_120px_96px] gap-4 border-b px-4 py-2.5 last:border-b-0 hover:bg-muted/20"
                  key={item.id}
                >
                  <button
                    className="flex min-w-0 items-center gap-3 text-left"
                    onClick={() => {
                      if (item.kind === 'folder') {
                        onGoToFolder(item.id)
                      }
                    }}
                    onDoubleClick={() => {
                      if (item.kind === 'folder') {
                        onGoToFolder(item.id)
                      }
                    }}
                    type="button"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border bg-muted">
                      {getItemIcon(item)}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-medium">{item.name}</p>
                    </div>
                  </button>
                  <span className="self-center text-sm text-muted-foreground">{t('common.ownerMe')}</span>
                  <span className="self-center text-sm text-muted-foreground">{formatDate(item.deletedAt, language)}</span>
                  <span className="self-center text-sm text-muted-foreground">
                    {item.kind === 'file' ? formatBytes(item.size) : formatBytes(item.cachedSize ?? 0)}
                  </span>
                  <span className="self-center text-sm text-muted-foreground">{getFileTypeLabel(item, t)}</span>
                  <div className="flex items-center justify-end gap-2">
                    <Button onClick={() => onRestore(item.id)} size="icon" variant="outline">
                      <RotateCcw className="h-4 w-4" />
                    </Button>
                    <Button
                      onClick={() => onDelete(item)}
                      size="icon"
                      variant="ghost"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TrashBrowser
