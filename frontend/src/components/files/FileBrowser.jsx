import { useState } from 'react'
import {
  FileIcon,
  FileSpreadsheet,
  FileText,
  Folder,
  Image as ImageIcon,
} from 'lucide-react'

import { formatBytes, formatDate, getFileTypeLabel } from '@/lib/utils'
import { useI18n } from '@/components/app/I18nProvider'
import ItemActionsMenu from '@/components/files/ItemActionsMenu'
import { Button } from '@/components/ui/button'

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
  if (currentFolderId === 'root') {
    return [{ id: 'root', name: t('files.myFiles') }]
  }

  const breadcrumb = []
  let pointer = foldersById[currentFolderId]

  while (pointer) {
    breadcrumb.unshift({ id: pointer.id, name: pointer.name })
    pointer = pointer.parentId ? foldersById[pointer.parentId] : null
  }

  return [{ id: 'root', name: t('files.myFiles') }, ...breadcrumb]
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
  onBulkMove,
  onBulkTrash,
  onBulkDownload,
  onSelectionChange,
  onTrash,
  selectedCount,
  selectedItemIds,
  view,
}) {
  const { language, t } = useI18n()
  const breadcrumbs = buildBreadcrumbs(foldersById, currentFolderId, t)
  const [draggedItem, setDraggedItem] = useState(null)
  const [dropTargetId, setDropTargetId] = useState(null)
  const selectedIdsSet = new Set(selectedItemIds)
  const allSelected = items.length > 0 && items.every((item) => selectedIdsSet.has(item.id))
  const partiallySelected = items.some((item) => selectedIdsSet.has(item.id)) && !allSelected

  const setSelectionForItem = (itemId, checked) => {
    if (checked) {
      onSelectionChange([...selectedIdsSet, itemId])
      return
    }

    onSelectionChange(selectedItemIds.filter((id) => id !== itemId))
  }

  const toggleSelectionForItem = (itemId) => {
    setSelectionForItem(itemId, !selectedIdsSet.has(itemId))
  }

  const toggleAllSelection = (checked) => {
    if (checked) {
      onSelectionChange(items.map((item) => item.id))
      return
    }

    onSelectionChange([])
  }

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
    <div className="space-y-3">
      {draggedItem ? (
        <div className="rounded-lg border border-dashed bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
          {t('files.selectionMovedHint', { name: draggedItem.name })}
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
          <p className="text-2xl font-semibold">{t('files.emptyTitle')}</p>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            {t('files.emptyDescription')}
          </p>
        </div>
      ) : null}

      {items.length > 0 && view === 'grid' ? (
        <div className="space-y-2.5">
          <div className="flex h-14 items-center justify-between rounded-lg border bg-background px-3">
            <label className="inline-flex items-center gap-2 text-sm text-foreground">
              <input
                aria-label={t('files.selectAll')}
                checked={allSelected}
                className="h-4 w-4 accent-primary"
                onChange={(event) => toggleAllSelection(event.target.checked)}
                ref={(element) => {
                  if (element) {
                    element.indeterminate = partiallySelected
                  }
                }}
                type="checkbox"
              />
              {t('files.selectedShort', { count: selectedCount })}
            </label>
            <div className="flex items-center gap-2">
              <Button disabled={selectedCount === 0} onClick={onBulkMove} size="sm" variant="outline">
                {t('common.move')}
              </Button>
              <Button disabled={selectedCount === 0} onClick={onBulkTrash} size="sm" variant="outline">
                {t('itemMenu.toTrash')}
              </Button>
              <Button disabled={selectedCount === 0} onClick={onBulkDownload} size="sm" variant="outline">
                {t('common.download')}
              </Button>
            </div>
          </div>

          <div className="grid gap-2.5 xl:grid-cols-4 2xl:grid-cols-5">
            {items.map((item) => (
              <div
                className={`relative rounded-xl border bg-background p-3 shadow-sm transition-colors hover:border-foreground/20 ${
                  selectedIdsSet.has(item.id)
                    ? 'border-primary/80 bg-primary/5'
                    : dropTargetId === item.id
                      ? 'border-primary bg-primary/5'
                      : ''
                }`}
                draggable
                key={item.id}
                onClick={() => toggleSelectionForItem(item.id)}
                onDoubleClick={() => {
                  item.kind === 'folder' ? onOpenFolder(item.id) : onPreview(item)
                }}
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
                <div className="flex items-start justify-between gap-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg border bg-muted">
                    {getItemIcon(item)}
                  </div>
                  <div
                    onClick={(event) => event.stopPropagation()}
                    onDoubleClick={(event) => event.stopPropagation()}
                  >
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

                <div className="mt-3 block w-full text-left">
                  <p className="truncate text-base font-semibold leading-tight">{item.name}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{getFileTypeLabel(item, t)}</p>
                </div>

                <div className="mt-3 flex items-center justify-between text-sm text-muted-foreground">
                  <span>{item.kind === 'file' ? formatBytes(item.size) : formatBytes(item.cachedSize ?? 0)}</span>
                  <span>{formatDate(item.updatedAt, language)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {items.length > 0 && view === 'list' ? (
        <div className="overflow-hidden rounded-lg border bg-background">
          <div className="max-h-[74vh] overflow-auto">
            <div className="min-w-[980px]">
              <div className="sticky top-0 z-20 grid h-14 grid-cols-[36px_minmax(0,2.8fr)_160px_190px_120px_72px] items-center gap-4 border-b bg-background/95 px-4 backdrop-blur">
                <span className="flex h-4 items-center">
                  <input
                    aria-label={t('files.selectAll')}
                    checked={allSelected}
                    className="h-4 w-4 accent-primary"
                    onChange={(event) => toggleAllSelection(event.target.checked)}
                    ref={(element) => {
                      if (element) {
                        element.indeterminate = partiallySelected
                      }
                    }}
                    type="checkbox"
                  />
                </span>

                {selectedCount > 0 ? (
                  <>
                    <span className="col-span-2 truncate text-sm leading-none text-foreground">
                      {t('files.selectedItems', { count: selectedCount })}
                    </span>
                    <div className="col-span-3 flex items-center justify-end gap-2 whitespace-nowrap">
                      <Button onClick={onBulkMove} size="sm" variant="outline">
                        {t('common.move')}
                      </Button>
                      <Button onClick={onBulkTrash} size="sm" variant="outline">
                        {t('itemMenu.toTrash')}
                      </Button>
                      <Button onClick={onBulkDownload} size="sm" variant="outline">
                        {t('common.download')}
                      </Button>
                    </div>
                  </>
                ) : (
                  <>
                    <span className="text-xs uppercase leading-none tracking-[0.18em] text-muted-foreground">{t('files.columns.name')}</span>
                    <span className="text-xs uppercase leading-none tracking-[0.18em] text-muted-foreground">{t('files.columns.owner')}</span>
                    <span className="text-xs uppercase leading-none tracking-[0.18em] text-muted-foreground">{t('files.columns.updated')}</span>
                    <span className="text-xs uppercase leading-none tracking-[0.18em] text-muted-foreground">{t('files.columns.size')}</span>
                    <span className="text-right text-xs uppercase leading-none tracking-[0.18em] text-muted-foreground">{t('files.columns.actions')}</span>
                  </>
                )}
              </div>
              {items.map((item) => (
                <div
                  className={`grid grid-cols-[36px_minmax(0,2.8fr)_160px_190px_120px_72px] gap-4 border-b px-4 py-2.5 last:border-b-0 ${
                    selectedIdsSet.has(item.id)
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
                    <input
                      aria-label={`${t('files.selectAll')}: ${item.name}`}
                      checked={selectedIdsSet.has(item.id)}
                      className="h-4 w-4 accent-primary"
                      onChange={(event) => setSelectionForItem(item.id, event.target.checked)}
                      type="checkbox"
                    />
                  </div>
                  <button
                    className="flex min-w-0 items-center gap-3 text-left"
                    onDoubleClick={() => {
                      item.kind === 'folder' ? onOpenFolder(item.id) : onPreview(item)
                    }}
                    onClick={() => toggleSelectionForItem(item.id)}
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
                  <span className="self-center text-sm text-muted-foreground">{formatDate(item.updatedAt, language)}</span>
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
