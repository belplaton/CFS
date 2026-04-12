import {
  FileIcon,
  FileSpreadsheet,
  FileText,
  Folder,
  Image as ImageIcon,
  MoreHorizontal,
  Pencil,
  Trash2,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { formatBytes, formatDate, getFileTypeLabel } from '@/lib/utils'

function getItemIcon(item) {
  if (item.kind === 'folder') {
    return <Folder className="h-5 w-5 text-sky-600" />
  }

  if (item.mimeType?.startsWith('image/')) {
    return <ImageIcon className="h-5 w-5 text-cyan-600" />
  }

  if (item.mimeType === 'application/pdf') {
    return <FileText className="h-5 w-5 text-rose-600" />
  }

  if (item.mimeType?.includes('sheet') || item.mimeType?.includes('excel')) {
    return <FileSpreadsheet className="h-5 w-5 text-emerald-600" />
  }

  return <FileIcon className="h-5 w-5 text-slate-500" />
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

function Actions({ item, onPreview, onRename, onTrash }) {
  return (
    <div className="flex items-center gap-1">
      {item.kind === 'folder' ? null : (
        <Button className="rounded-full" onClick={() => onPreview(item)} size="icon" variant="ghost">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      )}
      <Button className="rounded-full" onClick={() => onRename(item)} size="icon" variant="ghost">
        <Pencil className="h-4 w-4" />
      </Button>
      <Button className="rounded-full text-rose-600 hover:text-rose-700" onClick={() => onTrash(item)} size="icon" variant="ghost">
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  )
}

function FileBrowser({
  currentFolderId,
  foldersById,
  items,
  onGoToFolder,
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
            className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition hover:border-sky-300 hover:text-sky-700"
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
        <div className="rounded-[28px] border border-dashed border-slate-300 bg-white/70 px-6 py-16 text-center">
          <p className="text-2xl font-semibold">В этой папке пока пусто</p>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            Создайте папку, перетащите файлы или откройте поиск, чтобы проверить другие разделы.
          </p>
        </div>
      ) : null}

      {items.length > 0 && view === 'grid' ? (
        <div className="grid gap-4 xl:grid-cols-2 2xl:grid-cols-3">
          {items.map((item) => (
            <div
              className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-[0_10px_30px_rgba(148,163,184,0.08)]"
              key={item.id}
            >
              <div className="flex items-start justify-between gap-4">
                <div className={`flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br ${item.accent ?? 'from-slate-500 to-slate-400'} text-white`}>
                  {getItemIcon(item)}
                </div>
                <Actions item={item} onPreview={onPreview} onRename={onRename} onTrash={onTrash} />
              </div>

              <button
                className="mt-5 block text-left"
                onClick={() => (item.kind === 'folder' ? onOpenFolder(item.id) : onPreview(item))}
                type="button"
              >
                <p className="text-lg font-semibold">{item.name}</p>
                <p className="mt-2 text-sm text-slate-500">{getFileTypeLabel(item)}</p>
              </button>

              <div className="mt-5 flex items-center justify-between text-sm text-slate-500">
                <span>{item.kind === 'file' ? formatBytes(item.size) : 'Folder'}</span>
                <span>{formatDate(item.updatedAt)}</span>
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {items.length > 0 && view === 'list' ? (
        <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-white">
          <div className="overflow-x-auto">
            <div className="min-w-[760px]">
              <div className="grid grid-cols-[minmax(0,1.8fr)_140px_140px_100px] gap-4 border-b border-slate-200 px-6 py-4 text-xs uppercase tracking-[0.25em] text-slate-500">
                <span>Название</span>
                <span>Тип</span>
                <span>Размер</span>
                <span className="text-right">Действия</span>
              </div>
              {items.map((item) => (
                <div
                  className="grid grid-cols-[minmax(0,1.8fr)_140px_140px_100px] gap-4 border-b border-slate-100 px-6 py-4 last:border-b-0"
                  key={item.id}
                >
                  <button
                    className="flex min-w-0 items-center gap-3 text-left"
                    onClick={() => (item.kind === 'folder' ? onOpenFolder(item.id) : onPreview(item))}
                    type="button"
                  >
                    <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br ${item.accent ?? 'from-slate-500 to-slate-400'} text-white`}>
                      {getItemIcon(item)}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-medium">{item.name}</p>
                      <p className="text-sm text-slate-500">{formatDate(item.updatedAt)}</p>
                    </div>
                  </button>
                  <span className="self-center text-sm text-slate-600">{getFileTypeLabel(item)}</span>
                  <span className="self-center text-sm text-slate-600">
                    {item.kind === 'file' ? formatBytes(item.size) : '-'}
                  </span>
                  <div className="flex items-center justify-end">
                    <Actions item={item} onPreview={onPreview} onRename={onRename} onTrash={onTrash} />
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
