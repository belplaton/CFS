import { useDeferredValue, useEffect, useState } from 'react'
import {
  FolderPlus,
  Grid2X2,
  List,
  Search,
  UploadCloud,
} from 'lucide-react'

import FileBrowser from '@/components/files/FileBrowser'
import { useI18n } from '@/components/app/I18nProvider'
import LanguageSwitcher from '@/components/app/LanguageSwitcher'
import PreviewModal from '@/components/files/PreviewModal'
import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ROOT_FOLDER_ID } from '@/lib/files-constants'
import { buildFolderSizeCache, getItemEffectiveSize, matchesTypeFilter } from '@/lib/file-metrics'
import { canMoveItemToParent, getDescendantIds, useFileStore } from '@/store/file-store'

function buildFolderOptions(items, t, language, excludedIds = []) {
  const excluded = new Set(excludedIds)
  const folders = items.filter((item) => item.kind === 'folder' && !item.deletedAt && !excluded.has(item.id))
  const byParent = folders.reduce((accumulator, folder) => {
    const key = folder.parentId ?? ROOT_FOLDER_ID
    if (!accumulator[key]) {
      accumulator[key] = []
    }

    accumulator[key].push(folder)
    return accumulator
  }, {})

  const result = [{ id: ROOT_FOLDER_ID, label: t('files.myFiles') }]

  function walk(parentId, depth = 0) {
    const children = (byParent[parentId] ?? []).sort((left, right) => left.name.localeCompare(right.name, language))

    children.forEach((folder) => {
      result.push({
        id: folder.id,
        label: `${'— '.repeat(depth + 1)}${folder.name}`,
      })
      walk(folder.id, depth + 1)
    })
  }

  walk(ROOT_FOLDER_ID)
  return result
}

function getCurrentFolderTitle(currentFolderId, foldersById, t) {
  if (currentFolderId === ROOT_FOLDER_ID) {
    return t('files.myFiles')
  }

  return foldersById[currentFolderId]?.name ?? t('files.myFiles')
}

function ModalCard({ children, onClose, title, t }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl border bg-background p-6 shadow-2xl">
        <div className="flex items-center justify-between gap-4">
          <h3 className="text-2xl font-semibold">{title}</h3>
          <Button onClick={onClose} variant="ghost">
            {t('files.close')}
          </Button>
        </div>
        <div className="mt-6">{children}</div>
      </div>
    </div>
  )
}

function FilesPage() {
  const { language, t } = useI18n()
  const {
    allFolders,
    clearSearch,
    closePreview,
    createFolder,
    currentFolderId,
    downloadItem,
    fileError,
    isLoading,
    isMutating,
    isSearching,
    items,
    loadFolder,
    moveItems,
    moveItemsToTrash,
    moveToTrash,
    moveItem,
    openFolder,
    openPreview,
    previewItemId,
    renameItem,
    searchItems,
    searchQuery,
    searchResults,
    searchTotal,
    setSearchQuery,
    setSortBy,
    setView,
    sortBy,
    uploadFiles,
    view,
  } = useFileStore((state) => state)

  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [movingItems, setMovingItems] = useState([])
  const [renamingItem, setRenamingItem] = useState(null)
  const [selectedItemIds, setSelectedItemIds] = useState([])
  const [typeFilter, setTypeFilter] = useState('all')
  const deferredSearchQuery = useDeferredValue(searchQuery)
  const isSearchMode = deferredSearchQuery.trim().length > 0

  const foldersById = Object.fromEntries(allFolders.map((item) => [item.id, item]))
  const currentFolderTitle = getCurrentFolderTitle(currentFolderId, foldersById, t)
  const sourceItems = isSearchMode ? searchResults : items
  const folderSizeCache = buildFolderSizeCache(sourceItems)
  const visibleItems = sourceItems
    .filter((item) => matchesTypeFilter(item, typeFilter))
    .map((item) => ({
      ...item,
      cachedSize: getItemEffectiveSize(item, folderSizeCache),
    }))
    .sort((left, right) => {
      if (left.kind !== right.kind) {
        return left.kind === 'folder' ? -1 : 1
      }

      if (sortBy === 'name') {
        return left.name.localeCompare(right.name, language)
      }

      if (sortBy === 'nameDesc') {
        return right.name.localeCompare(left.name, language)
      }

      if (sortBy === 'size') {
        return (right.cachedSize ?? 0) - (left.cachedSize ?? 0)
      }

      if (sortBy === 'sizeAsc') {
        return (left.cachedSize ?? 0) - (right.cachedSize ?? 0)
      }

      if (sortBy === 'updatedAtAsc') {
        return new Date(left.updatedAt).getTime() - new Date(right.updatedAt).getTime()
      }

      return new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime()
    })

  const previewItem = sourceItems.find((item) => item.id === previewItemId) ?? items.find((item) => item.id === previewItemId) ?? null
  const selectedItems = visibleItems.filter((item) => selectedItemIds.includes(item.id))
  const moveOptions = movingItems.length
    ? buildFolderOptions(
        allFolders,
        t,
        language,
        movingItems.flatMap((item) =>
          item.kind === 'folder' ? [item.id, ...getDescendantIds(item.id)] : [item.id],
        ),
      )
    : []

  useEffect(() => {
    if (searchQuery.trim()) {
      return
    }

    void loadFolder(currentFolderId || ROOT_FOLDER_ID)
  }, [currentFolderId, loadFolder, searchQuery])

  useEffect(() => {
    if (!deferredSearchQuery.trim()) {
      void searchItems('')
      return
    }

    void searchItems(deferredSearchQuery)
  }, [deferredSearchQuery, searchItems])

  useEffect(() => {
    const visibleIds = new Set(visibleItems.map((item) => item.id))
    setSelectedItemIds((previous) => {
      const next = previous.filter((id) => visibleIds.has(id))
      if (next.length === previous.length && next.every((id, index) => id === previous[index])) {
        return previous
      }

      return next
    })
  }, [visibleItems])

  const clearSelection = () => {
    setSelectedItemIds([])
  }

  const handleOpenFolder = async (folderId) => {
    if (searchQuery) {
      clearSearch()
    }
    await openFolder(folderId)
  }

  const moveManyToTrash = () => {
    if (!selectedItems.length) {
      return
    }

    if (
      !window.confirm(
        t('files.confirmTrashMany', { count: selectedItems.length }),
      )
    ) {
      return
    }

    void moveItemsToTrash(selectedItems)
    clearSelection()
  }

  return (
    <div className="space-y-3">
      <input
        className="hidden"
        hidden
        id="file-upload-trigger"
        multiple
        onChange={async (event) => {
          await uploadFiles(Array.from(event.target.files ?? []), currentFolderId)
          event.target.value = ''
        }}
        type="file"
      />

      <section className="space-y-3 rounded-xl border bg-card p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{t('files.currentFolder')}</p>
            <h1 className="truncate text-[2rem] font-semibold tracking-tight">{currentFolderTitle}</h1>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Button
              onClick={() => setView('list')}
              size="icon"
              variant={view === 'list' ? 'default' : 'outline'}
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              onClick={() => setView('grid')}
              size="icon"
              variant={view === 'grid' ? 'default' : 'outline'}
            >
              <Grid2X2 className="h-4 w-4" />
            </Button>
            <select
              className="h-9 rounded-md border border-input bg-background px-3 text-sm shadow-sm"
              onChange={(event) => setSortBy(event.target.value)}
              value={sortBy}
            >
              <option value="updatedAt">{t('files.sort.updatedDesc')}</option>
              <option value="updatedAtAsc">{t('files.sort.updatedAsc')}</option>
              <option value="name">{t('files.sort.nameAsc')}</option>
              <option value="nameDesc">{t('files.sort.nameDesc')}</option>
              <option value="size">{t('files.sort.sizeDesc')}</option>
              <option value="sizeAsc">{t('files.sort.sizeAsc')}</option>
            </select>

            <LanguageSwitcher compact />
            <ThemeSwitcher compact />
          </div>
        </div>

        <div className="border-b" />

        <div className="flex flex-col gap-2 xl:flex-row xl:items-center xl:justify-between">
          <div className="relative min-w-[260px] flex-1">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="h-10 bg-background pl-11 shadow-sm"
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder={t('files.searchPlaceholder')}
              value={searchQuery}
            />
          </div>

          <select
            className="h-10 rounded-md border border-input bg-background px-3 text-sm shadow-sm"
            onChange={(event) => setTypeFilter(event.target.value)}
            value={typeFilter}
          >
            <option value="all">{t('files.typeFilter.all')}</option>
            <option value="folders">{t('files.typeFilter.folders')}</option>
            <option value="files">{t('files.typeFilter.files')}</option>
            <option value="images">{t('files.typeFilter.images')}</option>
            <option value="pdf">{t('files.typeFilter.pdf')}</option>
            <option value="documents">{t('files.typeFilter.documents')}</option>
            <option value="archives">{t('files.typeFilter.archives')}</option>
          </select>

          <div className="flex flex-wrap gap-2">
            <Button className="h-10 gap-2 px-4" disabled={isMutating} onClick={() => setIsCreateOpen(true)} variant="outline">
              <FolderPlus className="h-4 w-4" />
              {t('files.createFolderShort')}
            </Button>
            <Button className="h-10 gap-2 px-4" disabled={isMutating} onClick={() => document.getElementById('file-upload-trigger')?.click()}>
              <UploadCloud className="h-4 w-4" />
              {t('files.upload')}
            </Button>
          </div>
        </div>

        {fileError ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {fileError}
          </div>
        ) : null}
        {isSearchMode ? (
          <div className="rounded-lg border bg-muted/40 px-4 py-3 text-sm text-foreground">
            {t('files.searchResultsSummary', { query: deferredSearchQuery, count: searchTotal })}
          </div>
        ) : null}
        {isLoading ? (
          <div className="rounded-lg border bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
            {t('files.loading')}
          </div>
        ) : null}
        {isSearching ? (
          <div className="rounded-lg border bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
            {t('files.searchLoading')}
          </div>
        ) : null}
      </section>

      <FileBrowser
        canDropIntoFolder={(item, targetFolderId) => canMoveItemToParent(item.id, targetFolderId)}
        currentFolderId={currentFolderId}
        foldersById={foldersById}
        items={visibleItems}
        onDropIntoFolder={(item, targetFolderId) =>
          moveItem({
            id: item.id,
            kind: item.kind,
            parentId: targetFolderId,
          })}
        onGoToFolder={(folderId) => handleOpenFolder(folderId)}
        onMove={(item) => setMovingItems([item])}
        onOpenFolder={(folderId) => handleOpenFolder(folderId)}
        onPreview={(item) => openPreview(item.id)}
        onRename={(item) => setRenamingItem(item)}
        onBulkMove={() => setMovingItems(selectedItems)}
        onBulkTrash={moveManyToTrash}
        onBulkDownload={() => {
          selectedItems
            .filter((item) => item.kind === 'file')
            .forEach((item) => {
              void downloadItem(item)
            })
        }}
        onSelectionChange={setSelectedItemIds}
        onTrash={(item) => {
          if (window.confirm(t('files.confirmTrashSingle', { name: item.name }))) {
            void moveToTrash(item)
          }
        }}
        selectedCount={selectedItems.length}
        selectedItemIds={selectedItemIds}
        view={view}
      />

      {isCreateOpen ? (
        <ModalCard onClose={() => setIsCreateOpen(false)} t={t} title={t('files.createFolderTitle')}>
          <form
            className="space-y-4"
            onSubmit={async (event) => {
              event.preventDefault()
              const formData = new FormData(event.currentTarget)
              const name = formData.get('folderName')?.toString().trim()

              if (!name) {
                return
              }

              const success = await createFolder({
                name,
                parentId: currentFolderId,
              })
              if (success) {
                setIsCreateOpen(false)
              }
            }}
          >
            <Input autoFocus name="folderName" placeholder={t('files.folderNamePlaceholder')} />
            <Button className="w-full" disabled={isMutating} type="submit">
              {t('common.create')}
            </Button>
          </form>
        </ModalCard>
      ) : null}

      {movingItems.length ? (
        <ModalCard
          onClose={() => setMovingItems([])}
          t={t}
          title={movingItems.length > 1 ? t('files.moveManyTitle') : t('files.moveOneTitle')}
        >
          <form
            className="space-y-4"
            onSubmit={async (event) => {
              event.preventDefault()
              const formData = new FormData(event.currentTarget)
              const parentId = formData.get('parentId')?.toString() ?? ROOT_FOLDER_ID

              await moveItems({ items: movingItems, parentId })
              setMovingItems([])
              clearSelection()
            }}
          >
            <div className="rounded-lg border bg-muted/40 px-4 py-3 text-sm text-foreground">
              {movingItems.length > 1 ? (
                <>{t('files.movingCount', { count: movingItems.length })}</>
              ) : (
                <>{t('files.movingName', { name: movingItems[0].name })}</>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="move-parent">
                {t('files.targetFolder')}
              </label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                defaultValue={movingItems[0].parentId ?? ROOT_FOLDER_ID}
                id="move-parent"
                name="parentId"
              >
                {moveOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <Button className="w-full" disabled={isMutating} type="submit">
              {t('common.move')}
            </Button>
          </form>
        </ModalCard>
      ) : null}

      {renamingItem ? (
        <ModalCard onClose={() => setRenamingItem(null)} t={t} title={t('files.renameTitle')}>
          <form
            className="space-y-4"
            onSubmit={async (event) => {
              event.preventDefault()
              const formData = new FormData(event.currentTarget)
              const name = formData.get('itemName')?.toString().trim()

              if (!name) {
                return
              }

              await renameItem({
                id: renamingItem.id,
                kind: renamingItem.kind,
                name,
              })
              setRenamingItem(null)
            }}
          >
            <Input autoFocus defaultValue={renamingItem.name} name="itemName" />
            <Button className="w-full" disabled={isMutating} type="submit">
              {t('common.save')}
            </Button>
          </form>
        </ModalCard>
      ) : null}

      <PreviewModal item={previewItem} onClose={closePreview} onDownload={downloadItem} />
    </div>
  )
}

export default FilesPage

