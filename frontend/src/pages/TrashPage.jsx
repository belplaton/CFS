import { useEffect } from 'react'
import { RotateCcw, Trash2 } from 'lucide-react'

import { useI18n } from '@/components/app/I18nProvider'
import LanguageSwitcher from '@/components/app/LanguageSwitcher'
import ThemeSwitcher from '@/components/app/ThemeSwitcher'
import { Button } from '@/components/ui/button'
import { formatBytes, formatDate, getFileTypeLabel } from '@/lib/utils'
import { useFileStore } from '@/store/file-store'

function TrashPage() {
  const { language, t } = useI18n()
  const {
    deletePermanent,
    emptyTrash,
    fetchTrash,
    isTrashLoading,
    restoreItem,
    trashError,
    trashItems,
  } = useFileStore((state) => state)

  useEffect(() => {
    void fetchTrash()
  }, [fetchTrash])

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

      <section className="overflow-hidden rounded-xl border bg-card shadow-sm">
        <div className="overflow-x-auto">
          <div className="min-w-[820px]">
            <div className="grid grid-cols-[minmax(0,1.8fr)_140px_150px_170px] gap-4 border-b bg-muted/40 px-6 py-4 text-xs uppercase tracking-[0.2em] text-muted-foreground">
              <span>{t('trash.columns.name')}</span>
              <span>{t('trash.columns.type')}</span>
              <span>{t('trash.columns.deleted')}</span>
              <span className="text-right">{t('trash.columns.actions')}</span>
            </div>

            {trashItems.length === 0 ? (
              <div className="px-6 py-16 text-center">
                <p className="text-2xl font-semibold">{t('trash.emptyTitle')}</p>
                <p className="mt-3 text-sm leading-7 text-muted-foreground">
                  {t('trash.emptyDescription')}
                </p>
              </div>
            ) : null}

            {trashItems.map((item) => (
              <div
                className="grid grid-cols-[minmax(0,1.8fr)_140px_150px_170px] gap-4 border-b px-6 py-4 last:border-b-0 hover:bg-muted/20"
                key={item.id}
              >
                <div className="min-w-0">
                  <p className="truncate font-medium">{item.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {item.size ? formatBytes(item.size) : t('common.folder')}
                  </p>
                </div>
                <span className="self-center text-sm text-muted-foreground">{getFileTypeLabel(item, t)}</span>
                <span className="self-center text-sm text-muted-foreground">{formatDate(item.deletedAt, language)}</span>
                <div className="flex items-center justify-end gap-2">
                  <Button onClick={() => void restoreItem(item.id)} size="icon" variant="outline">
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                  <Button
                    onClick={() => {
                      if (window.confirm(t('trash.hardDeleteConfirm', { name: item.name }))) {
                        void deletePermanent(item.id)
                      }
                    }}
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
      </section>
    </div>
  )
}

export default TrashPage
