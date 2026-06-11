import { useEffect, useMemo, useState } from 'react'
import { Trash2 } from 'lucide-react'

import { useI18n } from '@/components/app/I18nProvider'
import LanguageSwitcher from '@/components/app/LanguageSwitcher'
import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import TrashBrowser from '@/components/files/TrashBrowser'
import { Button } from '@/components/ui/button'
import { ROOT_FOLDER_ID } from '@/lib/files-constants'
import { useFileStore } from '@/store/file-store'

function TrashPage() {
  const { t } = useI18n()
  const {
    deletePermanent,
    emptyTrash,
    fetchTrash,
    isTrashLoading,
    restoreItem,
    trashError,
    trashItems,
  } = useFileStore((state) => state)
  const [currentFolderId, setCurrentFolderId] = useState(ROOT_FOLDER_ID)

  useEffect(() => {
    void fetchTrash()
  }, [fetchTrash])

  const folderIds = useMemo(
    () => new Set(trashItems.filter((item) => item.kind === 'folder').map((item) => item.id)),
    [trashItems],
  )

  useEffect(() => {
    if (currentFolderId !== ROOT_FOLDER_ID && !folderIds.has(currentFolderId)) {
      setCurrentFolderId(ROOT_FOLDER_ID)
    }
  }, [currentFolderId, folderIds])

  return (
    <div className="space-y-6">
      <section className="rounded-xl border bg-card p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3 md:flex-nowrap">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">{t('trash.eyebrow')}</p>
            <h1 className="mt-3 text-3xl font-semibold">{t('trash.title')}</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground">
              {t('trash.description')}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Button
              className="gap-2"
              onClick={async () => {
                if (window.confirm(t('trash.emptyTrashConfirm'))) {
                  await emptyTrash()
                }
              }}
              variant="outline"
            >
              <Trash2 className="h-4 w-4" />
              {t('trash.emptyTrash')}
            </Button>
            <LanguageSwitcher compact />
            <ThemeSwitcher compact />
          </div>
        </div>
      </section>

      {trashError ? (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {trashError}
        </div>
      ) : null}
      {isTrashLoading ? (
        <div className="rounded-lg border bg-muted/40 px-4 py-3 text-sm text-muted-foreground">
          Loading trash...
        </div>
      ) : null}

      {trashItems.length === 0 ? (
        <section className="overflow-hidden rounded-xl border bg-card shadow-sm">
          <div className="px-6 py-16 text-center">
            <p className="text-2xl font-semibold">{t('trash.emptyTitle')}</p>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              {t('trash.emptyDescription')}
            </p>
          </div>
        </section>
      ) : (
        <TrashBrowser
          currentFolderId={currentFolderId}
          items={trashItems}
          onDelete={(item) => {
            if (window.confirm(t('trash.hardDeleteConfirm', { name: item.name }))) {
              void deletePermanent(item.id)
            }
          }}
          onGoToFolder={setCurrentFolderId}
          onRestore={(itemId) => void restoreItem(itemId)}
        />
      )}
    </div>
  )
}

export default TrashPage
