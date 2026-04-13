import { useState } from 'react'
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
  canDropIntoFolder,
  currentFolderId,
  foldersById,
  items,
  onDropIntoFolder,
  onGoToFolder,
  onMove,
  onOpenFolder,
  onPreview,
  onRename,
  onTrash,
  view,
}) {
  const breadcrumbs = buildBreadcrumbs(foldersById, currentFolderId)
  const [draggedItem, setDraggedItem] = useState(null)
  const [dropTargetId, setDropTargetId] = useState(null)
  const [selectedItemId, setSelectedItemId] = useState(null)

  const clearDragState = () => {
    setDraggedItem(null)
    setDropTargetId(null)
  }

  const handleDragStart = (item) => {
    setDraggedItem(item)
  }

  const handleDragOver = (event, targetFolderId) => {
    if (!draggedItem || !canDropIntoFolder(draggedItem, targetFolderId)) {
      return
    }

    event.preventDefault()
    if (dropTargetId !== targetFolderId) {
      setDropTargetId(targetFolderId)
    }
  }

  const handleDrop = (event, targetFolderId) => {
    event.preventDefault()

    if (!draggedItem || !canDropIntoFolder(draggedItem, targetFolderId)) {
      clearDragState()
      return
    }

    onDropIntoFolder(draggedItem, targetFolderId)
    clearDragState()
  }

  return (
    <div className="space-y-5">
      {draggedItem ? (
        <div className="rounded-lg border border-dashed bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
          Перемещение: <strong className="text-foreground">{draggedItem.name}</strong>. Перетащи
          элемент на папку или в breadcrumbs, чтобы сменить родительский каталог.
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-2">
        {breadcrumbs.map((crumb, index) => (
          <button
            className={`inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm transition-colors ${
              dropTargetId === crumb.id
                ? 'border-primary bg-primary/10 text-foreground'
                : 'bg-background text-muted-foreground hover:bg-muted hover:text-foreground'
            }`}
            key={crumb.id}
            onDragLeave={() => {
              if (dropTargetId === crumb.id) {
                setDropTargetId(null)
              }
            }}
            onDragOver={(event) => handleDragOver(event, crumb.id)}
            onDrop={(event) => handleDrop(event, crumb.id)}
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
              className={`rounded-xl border bg-background p-5 shadow-sm transition-colors hover:border-foreground/20 ${
                dropTargetId === item.id ? 'border-primary bg-primary/5' : ''
              }`}
              draggable
              key={item.id}
              onDragEnd={clearDragState}
              onDragLeave={() => {
                if (dropTargetId === item.id) {
                  setDropTargetId(null)
                }
              }}
              onDragOver={item.kind === 'folder' ? (event) => handleDragOver(event, item.id) : undefined}
              onDragStart={() => handleDragStart(item)}
              onDrop={item.kind === 'folder' ? (event) => handleDrop(event, item.id) : undefined}
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
                onDoubleClick={() => {
                  item.kind === 'folder' ? onOpenFolder(item.id) : onPreview(item)
                }}
                onClick={() => setSelectedItemId(item.id)}
                type="button"
              >
                <p className="text-lg font-semibold">{item.name}</p>
                <p className="mt-2 text-sm text-muted-foreground">{getFileTypeLabel(item)}</p>
              </button>

              <div className="mt-5 flex items-center justify-between text-sm text-muted-foreground">
                <span>{item.kind === 'file' ? formatBytes(item.size) : formatBytes(item.cachedSize ?? 0)}</span>
                <span>{formatDate(item.updatedAt)}</span>
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {items.length > 0 && view === 'list' ? (
        <div className="overflow-hidden rounded-lg border bg-background">
          <div className="max-h-[74vh] overflow-auto">
            <div className="min-w-[980px]">
              <div className="sticky top-0 z-10 grid grid-cols-[36px_minmax(0,2.8fr)_160px_190px_120px_72px] gap-4 border-b bg-background/95 px-4 py-3 text-xs uppercase tracking-[0.18em] text-muted-foreground backdrop-blur">
                <span />
                <span>Название</span>
                <span>Владелец</span>
                <span>Изменён</span>
                <span>Размер</span>
                <span className="text-right">Действия</span>
              </div>
              {items.map((item) => (
                <div
                  className={`grid grid-cols-[36px_minmax(0,2.8fr)_160px_190px_120px_72px] gap-4 border-b px-4 py-2 last:border-b-0 ${
                    selectedItemId === item.id
                      ? 'bg-muted/50'
                      : dropTargetId === item.id
                        ? 'bg-primary/5'
                        : 'hover:bg-muted/20'
                  }`}
                  draggable
                  key={item.id}
                  onDragEnd={clearDragState}
                  onDragLeave={() => {
                    if (dropTargetId === item.id) {
                      setDropTargetId(null)
                    }
                  }}
                  onDragOver={item.kind === 'folder' ? (event) => handleDragOver(event, item.id) : undefined}
                  onDragStart={() => handleDragStart(item)}
                  onDrop={item.kind === 'folder' ? (event) => handleDrop(event, item.id) : undefined}
                >
                  <div className="flex items-center">
                    <div
                      className={`h-4 w-4 rounded-sm border transition-colors ${
                        selectedItemId === item.id ? 'border-primary bg-primary' : 'border-border bg-background'
                      }`}
                    />
                  </div>
                  <button
                    className="flex min-w-0 items-center gap-3 text-left"
                    onDoubleClick={() => {
                      item.kind === 'folder' ? onOpenFolder(item.id) : onPreview(item)
                    }}
                    onClick={() => setSelectedItemId(item.id)}
                    type="button"
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border bg-muted">
                      {getItemIcon(item)}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-medium">{item.name}</p>
                    </div>
                  </button>
                  <span className="self-center text-sm text-muted-foreground">me</span>
                  <span className="self-center text-sm text-muted-foreground">{formatDate(item.updatedAt)}</span>
                  <span className="self-center text-sm text-muted-foreground">
                    {item.kind === 'file' ? formatBytes(item.size) : formatBytes(item.cachedSize ?? 0)}
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
