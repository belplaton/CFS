import { useDeferredValue, useEffect, useState } from 'react'
import {
  FolderPlus,
  FolderTree,
  Grid2X2,
  List,
  Search,
  Sparkles,
  Trash2,
  UploadCloud,
} from 'lucide-react'

import FileBrowser from '@/components/files/FileBrowser'
import PreviewModal from '@/components/files/PreviewModal'
import QuotaCard from '@/components/files/QuotaCard'
import UploadDropzone from '@/components/files/UploadDropzone'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ROOT_FOLDER_ID } from '@/data/mock-data'
import { formatBytes } from '@/lib/utils'
import { useAuthStore } from '@/store/auth-store'
import { getDescendantIds, getUsedBytes, useFileStore } from '@/store/file-store'

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
  const user = useAuthStore((state) => state.user)
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
  const [movingItem, setMovingItem] = useState(null)
  const [renamingItem, setRenamingItem] = useState(null)
  const deferredSearchQuery = useDeferredValue(searchQuery)

  useEffect(() => {
    ensureSeedData()
  }, [ensureSeedData])

  const foldersById = Object.fromEntries(items.filter((item) => item.kind === 'folder').map((item) => [item.id, item]))
  const normalizedCurrentFolderId = currentFolderId === ROOT_FOLDER_ID ? null : currentFolderId
  const visibleItems = items
    .filter((item) => !item.deletedAt && item.parentId === normalizedCurrentFolderId)
    .filter((item) =>
      deferredSearchQuery
        ? item.name.toLowerCase().includes(deferredSearchQuery.toLowerCase())
        : true,
    )
    .sort((left, right) => {
      if (left.kind !== right.kind) {
        return left.kind === 'folder' ? -1 : 1
      }

      if (sortBy === 'name') {
        return left.name.localeCompare(right.name, 'ru')
      }

      if (sortBy === 'size') {
        return (right.size ?? 0) - (left.size ?? 0)
      }

      return new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime()
    })

  const previewItem = items.find((item) => item.id === previewItemId) ?? null
  const usedBytes = getUsedBytes()
  const trashCount = items.filter((item) => item.deletedAt).length
  const folderCount = items.filter((item) => item.kind === 'folder' && !item.deletedAt).length
  const fileCount = items.filter((item) => item.kind === 'file' && !item.deletedAt).length
  const moveOptions = movingItem
    ? buildFolderOptions(
        items,
        movingItem.kind === 'folder' ? [movingItem.id, ...getDescendantIds(movingItem.id)] : [],
      )
    : []

  const overviewCards = [
    {
      id: 'folders',
      icon: FolderTree,
      label: 'Структура папок',
      value: folderCount,
      description: 'активных папок',
    },
    {
      id: 'files',
      icon: UploadCloud,
      label: 'Контент',
      value: fileCount,
      description: 'активных файлов',
    },
    {
      id: 'trash',
      icon: Trash2,
      label: 'Корзина',
      value: trashCount,
      description: 'элементов ожидают решения',
    },
  ]

  return (
    <div className="space-y-6">
      <section className="rounded-xl border bg-card p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-md border bg-muted px-3 py-1.5 text-sm text-muted-foreground">
              <Sparkles className="h-4 w-4" />
              Frontend workspace
            </div>
            <h1 className="mt-4 text-3xl font-semibold tracking-tight md:text-4xl">Файловый менеджер</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground md:text-base">
              Главный сценарий экрана теперь собран вокруг рабочего пространства с файлами и папками.
              Квота, быстрые действия и статусные блоки остаются рядом, но не забирают первичный фокус.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button className="gap-2" onClick={() => setIsCreateOpen(true)}>
              <FolderPlus className="h-4 w-4" />
              Создать папку
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_360px]">
        <div className="grid gap-4 md:grid-cols-3">
          {overviewCards.map((card) => {
            const Icon = card.icon

            return (
              <Card className="border bg-card shadow-sm" key={card.id}>
                <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{card.label}</p>
                    <CardTitle className="mt-3 text-3xl font-semibold">{card.value}</CardTitle>
                  </div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg border bg-muted">
                    <Icon className="h-5 w-5 text-foreground" />
                  </div>
                </CardHeader>
                <CardContent className="pt-0 text-sm text-muted-foreground">{card.description}</CardContent>
              </Card>
            )
          })}
        </div>

        <QuotaCard plan={user?.plan ?? 'Free'} quotaBytes={user?.quotaBytes ?? 1} usedBytes={usedBytes} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.55fr)_360px]">
        <div className="rounded-xl border bg-card p-6 shadow-sm md:p-8">
          <div className="border-b pb-6">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div className="max-w-2xl">
                <div className="inline-flex items-center gap-2 rounded-md border bg-muted px-3 py-1.5 text-sm text-muted-foreground">
                  <Sparkles className="h-4 w-4" />
                  Current focus
                </div>
                <h2 className="mt-4 text-2xl font-semibold tracking-tight">Файлы и папки</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Основное рабочее пространство: поиск, сортировка, навигация по папкам и действия над
                  элементами сосредоточены в одном блоке без лишнего визуального шума.
                </p>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={() => setView('grid')}
                  size="icon"
                  variant={view === 'grid' ? 'default' : 'outline'}
                >
                  <Grid2X2 className="h-4 w-4" />
                </Button>
                <Button
                  onClick={() => setView('list')}
                  size="icon"
                  variant={view === 'list' ? 'default' : 'outline'}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="mt-5 flex flex-col gap-3 xl:flex-row xl:items-center">
              <div className="relative min-w-[260px] flex-1">
                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="bg-background pl-11 shadow-sm"
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Поиск по текущей папке"
                  value={searchQuery}
                />
              </div>

              <select
                className="h-10 rounded-md border border-input bg-background px-4 text-sm shadow-sm"
                onChange={(event) => setSortBy(event.target.value)}
                value={sortBy}
              >
                <option value="updatedAt">Сначала новые</option>
                <option value="name">По имени</option>
                <option value="size">По размеру</option>
              </select>
            </div>
          </div>

          <div className="mt-4 rounded-lg border bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
            Использовано {formatBytes(usedBytes)}. По мере готовности backend сюда подключаются quota
            endpoint, реальные uploads и preview/download URL.
          </div>

          <div className="mt-6">
            <FileBrowser
              currentFolderId={currentFolderId}
              foldersById={foldersById}
              items={visibleItems}
              onGoToFolder={(folderId) => openFolder(folderId)}
              onMove={(item) => setMovingItem(item)}
              onOpenFolder={(folderId) => openFolder(folderId)}
              onPreview={(item) => openPreview(item.id)}
              onRename={(item) => setRenamingItem(item)}
              onTrash={(item) => {
                if (window.confirm(`Переместить "${item.name}" в корзину?`)) {
                  moveToTrash(item.id)
                }
              }}
              view={view}
            />
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border bg-card p-6 shadow-sm">
            <div className="mb-4">
              <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Quick actions</p>
              <h2 className="mt-3 text-xl font-semibold">Загрузка и структура</h2>
            </div>

            <UploadDropzone
              compact
              onCreateFolder={() => setIsCreateOpen(true)}
              onFilesSelected={(files) => uploadFiles(files, currentFolderId)}
            />
          </div>

          <div className="rounded-xl border bg-card p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">UX focus</p>
            <h2 className="mt-3 text-xl font-semibold">Куда смотреть пользователю</h2>

            <div className="mt-5 space-y-4">
              <div className="rounded-lg border bg-muted/40 p-4">
                <p className="text-sm font-medium">Первичный фокус</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Основной список файлов и навигация по папкам находятся в центральной рабочей зоне.
                </p>
              </div>

              <div className="rounded-lg border bg-muted/40 p-4">
                <p className="text-sm font-medium">Вторичный контекст</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Квота, загрузка и быстрые действия вынесены в правую колонку, чтобы не спорить с
                  основным сценарием.
                </p>
              </div>

              <div className="rounded-lg border bg-muted/40 p-4">
                <p className="text-sm font-medium">Следующий фронтендовый шаг</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Довести interaction states, drag & drop перемещение и финальную консистентность preview.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

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

      {movingItem ? (
        <ModalCard onClose={() => setMovingItem(null)} title="Переместить элемент">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault()
              const formData = new FormData(event.currentTarget)
              const parentId = formData.get('parentId')?.toString() ?? ROOT_FOLDER_ID

              moveItem({
                id: movingItem.id,
                parentId,
              })
              setMovingItem(null)
            }}
          >
            <div className="rounded-lg border bg-muted/40 px-4 py-3 text-sm text-foreground">
              Перемещаем: <strong>{movingItem.name}</strong>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="move-parent">
                Целевая папка
              </label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                defaultValue={movingItem.parentId ?? ROOT_FOLDER_ID}
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

