import {
  FileIcon,
  FileSpreadsheet,
  FileText,
  Folder,
  Image as ImageIcon,
} from 'lucide-react'

import { formatBytes, formatDate, getFileTypeLabel } from '@/lib/utils'
import ItemActionsMenu from '@/components/files/ItemActionsMenu'

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

function buildBreadcrumbs(foldersById, currentFolderId) {
  if (currentFolderId === 'root') {
    return [{ id: 'root', name: 'My Files' }]
  }

  const breadcrumb = []
  let pointer = foldersById[currentFolderId]

  while (pointer) {
    breadcrumb.unshift({ id: pointer.id, name: pointer.name })
    pointer = pointer.parentId ? foldersById[pointer.parentId] : null
  }

  return [{ id: 'root', name: 'My Files' }, ...breadcrumb]
}

function FileBrowser({
  currentFolderId,
  foldersById,
  items,
  onGoToFolder,
  onMove,
  onOpenFolder,
  onPreview,
  onRename,
  onTrash,
  view,
}) {
  const breadcrumbs = buildBreadcrumbs(foldersById, currentFolderId)

  return (
    <div className="space-y-5">
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

      {items.length === 0 ? (
        <div className="rounded-xl border border-dashed bg-muted/20 px-6 py-16 text-center">
          <p className="text-2xl font-semibold">В этой папке пока пусто</p>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            Создайте папку, перетащите файлы или откройте поиск, чтобы проверить другие разделы.
          </p>
        </div>
      ) : null}

      {items.length > 0 && view === 'grid' ? (
        <div className="grid gap-4 xl:grid-cols-2 2xl:grid-cols-3">
          {items.map((item) => (
            <div
              className="rounded-xl border bg-background p-5 shadow-sm transition-colors hover:border-foreground/20"
              key={item.id}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg border bg-muted">
                  {getItemIcon(item)}
                </div>
                <ItemActionsMenu
                  item={item}
                  onMove={() => onMove(item)}
                  onOpen={() => onOpenFolder(item.id)}
                  onPreview={() => onPreview(item)}
                  onRename={() => onRename(item)}
                  onTrash={() => onTrash(item)}
                />
              </div>

              <button
                className="mt-5 block text-left"
                onClick={() => (item.kind === 'folder' ? onOpenFolder(item.id) : onPreview(item))}
                type="button"
              >
                <p className="text-lg font-semibold">{item.name}</p>
                <p className="mt-2 text-sm text-muted-foreground">{getFileTypeLabel(item)}</p>
              </button>

              <div className="mt-5 flex items-center justify-between text-sm text-muted-foreground">
                <span>{item.kind === 'file' ? formatBytes(item.size) : 'Folder'}</span>
                <span>{formatDate(item.updatedAt)}</span>
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {items.length > 0 && view === 'list' ? (
        <div className="overflow-hidden rounded-xl border bg-background shadow-sm">
          <div className="overflow-x-auto">
            <div className="min-w-[760px]">
              <div className="grid grid-cols-[minmax(0,1.8fr)_140px_140px_100px] gap-4 border-b bg-muted/40 px-6 py-4 text-xs uppercase tracking-[0.2em] text-muted-foreground">
                <span>Название</span>
                <span>Тип</span>
                <span>Размер</span>
                <span className="text-right">Действия</span>
              </div>
              {items.map((item) => (
                <div
                  className="grid grid-cols-[minmax(0,1.8fr)_140px_140px_100px] gap-4 border-b px-6 py-4 last:border-b-0 hover:bg-muted/20"
                  key={item.id}
                >
                  <button
                    className="flex min-w-0 items-center gap-3 text-left"
                    onClick={() => (item.kind === 'folder' ? onOpenFolder(item.id) : onPreview(item))}
                    type="button"
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
                      {getItemIcon(item)}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-medium">{item.name}</p>
                      <p className="text-sm text-muted-foreground">{formatDate(item.updatedAt)}</p>
                    </div>
                  </button>
                  <span className="self-center text-sm text-muted-foreground">{getFileTypeLabel(item)}</span>
                  <span className="self-center text-sm text-muted-foreground">
                    {item.kind === 'file' ? formatBytes(item.size) : '-'}
                  </span>
                  <div className="flex items-center justify-end">
                    <ItemActionsMenu
                      item={item}
                      onMove={() => onMove(item)}
                      onOpen={() => onOpenFolder(item.id)}
                      onPreview={() => onPreview(item)}
                      onRename={() => onRename(item)}
                      onTrash={() => onTrash(item)}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export default FileBrowser
