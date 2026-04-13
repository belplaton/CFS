import { useDeferredValue, useEffect, useState } from 'react'
import {
  FolderPlus,
  Grid2X2,
  List,
  Search,
  UploadCloud,
} from 'lucide-react'

import FileBrowser from '@/components/files/FileBrowser'
import PreviewModal from '@/components/files/PreviewModal'
import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ROOT_FOLDER_ID } from '@/data/mock-data'
import { buildFolderSizeCache, getItemEffectiveSize, matchesTypeFilter } from '@/lib/file-metrics'
import { canMoveItemToParent, getDescendantIds, useFileStore } from '@/store/file-store'

function buildFolderOptions(items, excludedIds = []) {
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

  const result = [{ id: ROOT_FOLDER_ID, label: 'My Files' }]

  function walk(parentId, depth = 0) {
    const children = (byParent[parentId] ?? []).sort((left, right) => left.name.localeCompare(right.name, 'ru'))

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

function getCurrentFolderTitle(currentFolderId, foldersById) {
  if (currentFolderId === ROOT_FOLDER_ID) {
    return 'My Files'
  }

  return foldersById[currentFolderId]?.name ?? 'My Files'
}

function ModalCard({ children, onClose, title }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-xl border bg-background p-6 shadow-2xl">
        <div className="flex items-center justify-between gap-4">
          <h3 className="text-2xl font-semibold">{title}</h3>
          <Button onClick={onClose} variant="ghost">
            Закрыть
          </Button>
        </div>
        <div className="mt-6">{children}</div>
      </div>
    </div>
  )
}

function FilesPage() {
  const {
    closePreview,
    createFolder,
    currentFolderId,
    ensureSeedData,
    items,
    moveToTrash,
    moveItem,
    openFolder,
    openPreview,
    previewItemId,
    renameItem,
    searchQuery,
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

  useEffect(() => {
    ensureSeedData()
  }, [ensureSeedData])

  const foldersById = Object.fromEntries(items.filter((item) => item.kind === 'folder').map((item) => [item.id, item]))
  const currentFolderTitle = getCurrentFolderTitle(currentFolderId, foldersById)
  const normalizedCurrentFolderId = currentFolderId === ROOT_FOLDER_ID ? null : currentFolderId
  const folderSizeCache = buildFolderSizeCache(items)
  const visibleItems = items
    .filter((item) => !item.deletedAt && item.parentId === normalizedCurrentFolderId)
    .filter((item) =>
      deferredSearchQuery
        ? item.name.toLowerCase().includes(deferredSearchQuery.toLowerCase())
        : true,
    )
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
        return left.name.localeCompare(right.name, 'ru')
      }

      if (sortBy === 'nameDesc') {
        return right.name.localeCompare(left.name, 'ru')
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

  const previewItem = items.find((item) => item.id === previewItemId) ?? null
  const selectedItems = visibleItems.filter((item) => selectedItemIds.includes(item.id))
  const moveOptions = movingItems.length
    ? buildFolderOptions(
        items,
        movingItems.flatMap((item) =>
          item.kind === 'folder' ? [item.id, ...getDescendantIds(item.id)] : [item.id],
        ),
      )
    : []

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

  const moveManyToTrash = () => {
    if (!selectedItems.length) {
      return
    }

    if (
      !window.confirm(
        `Переместить ${selectedItems.length} элемент(ов) в корзину?`,
      )
    ) {
      return
    }

    selectedItems.forEach((item) => moveToTrash(item.id))
    clearSelection()
  }

  return (
    <div className="space-y-3">
      <input
        className="hidden"
        id="file-upload-trigger"
        multiple
        onChange={(event) => uploadFiles(Array.from(event.target.files ?? []), currentFolderId)}
        type="file"
      />

      <div className="sticky top-0 z-30 space-y-2 border-b bg-background/95 pb-3 pt-1 backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Current folder</p>
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
              <option value="updatedAt">Сначала новые</option>
              <option value="updatedAtAsc">Сначала старые</option>
              <option value="name">По имени</option>
              <option value="nameDesc">По имени (Z-A)</option>
              <option value="size">По размеру</option>
              <option value="sizeAsc">По размеру (малые)</option>
            </select>

            <ThemeSwitcher compact settingsMode />
          </div>
        </div>

        <div className="flex flex-col gap-2 xl:flex-row xl:items-center xl:justify-between">
          <div className="relative min-w-[260px] flex-1">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="h-10 bg-background pl-11 shadow-sm"
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Поиск по текущей папке"
              value={searchQuery}
            />
          </div>

          <select
            className="h-10 rounded-md border border-input bg-background px-3 text-sm shadow-sm"
            onChange={(event) => setTypeFilter(event.target.value)}
            value={typeFilter}
          >
            <option value="all">Все типы</option>
            <option value="folders">Папки</option>
            <option value="files">Файлы</option>
            <option value="images">Изображения</option>
            <option value="pdf">PDF</option>
            <option value="documents">Документы</option>
            <option value="archives">Архивы</option>
          </select>

          <div className="flex flex-wrap gap-2">
            <Button className="h-10 gap-2 px-4" onClick={() => setIsCreateOpen(true)} variant="outline">
              <FolderPlus className="h-4 w-4" />
              Папка
            </Button>
            <Button className="h-10 gap-2 px-4" onClick={() => document.getElementById('file-upload-trigger')?.click()}>
              <UploadCloud className="h-4 w-4" />
              Загрузить
            </Button>
          </div>
        </div>
      </div>

      <FileBrowser
        canDropIntoFolder={(item, targetFolderId) => canMoveItemToParent(item.id, targetFolderId)}
        currentFolderId={currentFolderId}
        foldersById={foldersById}
        items={visibleItems}
        onDropIntoFolder={(item, targetFolderId) =>
          moveItem({
            id: item.id,
            parentId: targetFolderId,
          })}
        onGoToFolder={(folderId) => openFolder(folderId)}
        onMove={(item) => setMovingItems([item])}
        onOpenFolder={(folderId) => openFolder(folderId)}
        onPreview={(item) => openPreview(item.id)}
        onRename={(item) => setRenamingItem(item)}
        onBulkMove={() => setMovingItems(selectedItems)}
        onBulkTrash={moveManyToTrash}
        onBulkDownload={() => window.alert('Массовое скачивание включим после подключения API архивации.')}
        onSelectionChange={setSelectedItemIds}
        onTrash={(item) => {
          if (window.confirm(`Переместить "${item.name}" в корзину?`)) {
            moveToTrash(item.id)
          }
        }}
        selectedCount={selectedItems.length}
        selectedItemIds={selectedItemIds}
        view={view}
      />

      {isCreateOpen ? (
        <ModalCard onClose={() => setIsCreateOpen(false)} title="Создать папку">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault()
              const formData = new FormData(event.currentTarget)
              const name = formData.get('folderName')?.toString().trim()

              if (!name) {
                return
              }

              createFolder({
                name,
                parentId: currentFolderId,
              })
              setIsCreateOpen(false)
            }}
          >
            <Input autoFocus name="folderName" placeholder="Например, Invoices" />
            <Button className="w-full" type="submit">
              Создать
            </Button>
          </form>
        </ModalCard>
      ) : null}

      {movingItems.length ? (
        <ModalCard
          onClose={() => setMovingItems([])}
          title={movingItems.length > 1 ? 'Переместить элементы' : 'Переместить элемент'}
        >
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault()
              const formData = new FormData(event.currentTarget)
              const parentId = formData.get('parentId')?.toString() ?? ROOT_FOLDER_ID

              movingItems.forEach((item) => {
                moveItem({
                  id: item.id,
                  parentId,
                })
              })

              setMovingItems([])
              clearSelection()
            }}
          >
            <div className="rounded-lg border bg-muted/40 px-4 py-3 text-sm text-foreground">
              {movingItems.length > 1 ? (
                <>
                  Перемещаем элементов: <strong>{movingItems.length}</strong>
                </>
              ) : (
                <>
                  Перемещаем: <strong>{movingItems[0].name}</strong>
                </>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="move-parent">
                Целевая папка
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

            <Button className="w-full" type="submit">
              Переместить
            </Button>
          </form>
        </ModalCard>
      ) : null}

      {renamingItem ? (
        <ModalCard onClose={() => setRenamingItem(null)} title="Переименовать">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault()
              const formData = new FormData(event.currentTarget)
              const name = formData.get('itemName')?.toString().trim()

              if (!name) {
                return
              }

              renameItem({
                id: renamingItem.id,
                name,
              })
              setRenamingItem(null)
            }}
          >
            <Input autoFocus defaultValue={renamingItem.name} name="itemName" />
            <Button className="w-full" type="submit">
              Сохранить
            </Button>
          </form>
        </ModalCard>
      ) : null}

      <PreviewModal item={previewItem} onClose={closePreview} />
    </div>
  )
}

export default FilesPage

