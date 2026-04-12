import { useDeferredValue, useEffect, useState } from 'react'
import { FolderPlus, Grid2X2, List, Search, Sparkles } from 'lucide-react'

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
import { getUsedBytes, useFileStore } from '@/store/file-store'

function ModalCard({ children, onClose, title }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-[32px] border border-white/70 bg-white p-6 shadow-[0_30px_90px_rgba(15,23,42,0.28)]">
        <div className="flex items-center justify-between gap-4">
          <h3 className="text-2xl font-semibold">{title}</h3>
          <Button className="rounded-full" onClick={onClose} variant="ghost">
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

  return (
    <div className="space-y-6">
      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[32px] border border-slate-200 bg-white p-6 shadow-[0_15px_40px_rgba(148,163,184,0.12)] md:p-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-200 bg-cyan-50 px-4 py-2 text-sm text-cyan-900">
            <Sparkles className="h-4 w-4" />
            Week 3-7 frontend scope consolidated
          </div>
          <h1 className="mt-5 text-3xl font-semibold md:text-5xl">Файловый менеджер и рабочий поток</h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-600 md:text-base">
            Здесь уже собраны базовые задачи по roadmap для фронтенда: layout, файловый список,
            search/sort, quota, корзина, preview и подготовка под future auth/preview integration.
          </p>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <Card className="rounded-[28px] border-slate-200 shadow-none">
              <CardHeader>
                <CardTitle className="text-lg">{folderCount}</CardTitle>
              </CardHeader>
              <CardContent className="pt-0 text-sm text-slate-600">активных папок</CardContent>
            </Card>
            <Card className="rounded-[28px] border-slate-200 shadow-none">
              <CardHeader>
                <CardTitle className="text-lg">{fileCount}</CardTitle>
              </CardHeader>
              <CardContent className="pt-0 text-sm text-slate-600">активных файлов</CardContent>
            </Card>
            <Card className="rounded-[28px] border-slate-200 shadow-none">
              <CardHeader>
                <CardTitle className="text-lg">{trashCount}</CardTitle>
              </CardHeader>
              <CardContent className="pt-0 text-sm text-slate-600">элементов в корзине</CardContent>
            </Card>
          </div>
        </div>

        <QuotaCard plan={user?.plan ?? 'Free'} quotaBytes={user?.quotaBytes ?? 1} usedBytes={usedBytes} />
      </section>

      <UploadDropzone
        onCreateFolder={() => setIsCreateOpen(true)}
        onFilesSelected={(files) => uploadFiles(files, currentFolderId)}
      />

      <section className="rounded-[32px] border border-slate-200 bg-white p-6 shadow-[0_15px_40px_rgba(148,163,184,0.12)] md:p-8">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-1 flex-wrap gap-3">
            <div className="relative min-w-[260px] flex-1">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                className="rounded-full border-slate-200 pl-11"
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Поиск по текущей папке"
                value={searchQuery}
              />
            </div>

            <select
              className="h-10 rounded-full border border-slate-200 bg-white px-4 text-sm"
              onChange={(event) => setSortBy(event.target.value)}
              value={sortBy}
            >
              <option value="updatedAt">Сначала новые</option>
              <option value="name">По имени</option>
              <option value="size">По размеру</option>
            </select>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button className="gap-2 rounded-full" onClick={() => setIsCreateOpen(true)} variant="outline">
              <FolderPlus className="h-4 w-4" />
              Папка
            </Button>
            <Button className="rounded-full" onClick={() => setView('grid')} size="icon" variant={view === 'grid' ? 'default' : 'outline'}>
              <Grid2X2 className="h-4 w-4" />
            </Button>
            <Button className="rounded-full" onClick={() => setView('list')} size="icon" variant={view === 'list' ? 'default' : 'outline'}>
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="mt-4 rounded-[24px] border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          Использовано {formatBytes(usedBytes)}. По мере готовности backend сюда подключаются quota
          endpoint, реальные uploads и preview/download URL.
        </div>

        <div className="mt-6">
          <FileBrowser
            currentFolderId={currentFolderId}
            foldersById={foldersById}
            items={visibleItems}
            onGoToFolder={(folderId) => openFolder(folderId)}
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
            <Button className="w-full rounded-full" type="submit">
              Создать
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
            <Button className="w-full rounded-full" type="submit">
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

