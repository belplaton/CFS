import { RotateCcw, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { formatBytes, formatDate, getFileTypeLabel } from '@/lib/utils'
import { useFileStore } from '@/store/file-store'

function TrashPage() {
  const { deletePermanent, emptyTrash, items, restoreItem } = useFileStore((state) => state)
  const trashItems = items.filter((item) => item.deletedAt)

  return (
    <div className="space-y-6">
      <section className="rounded-xl border bg-card p-6 shadow-sm md:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Trash</p>
            <h1 className="mt-3 text-3xl font-semibold">Корзина</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-muted-foreground">
              Отдельная страница корзины закрывает спринт 5 по roadmap. Восстановление и
              безвозвратное удаление уже отрисованы на уровне интерфейса и store.
            </p>
          </div>
          <Button
            className="gap-2"
            onClick={() => {
              if (window.confirm('Очистить корзину полностью?')) {
                emptyTrash()
              }
            }}
            variant="outline"
          >
            <Trash2 className="h-4 w-4" />
            Очистить корзину
          </Button>
        </div>
      </section>

      <section className="overflow-hidden rounded-xl border bg-card shadow-sm">
        <div className="overflow-x-auto">
          <div className="min-w-[820px]">
            <div className="grid grid-cols-[minmax(0,1.8fr)_140px_150px_170px] gap-4 border-b bg-muted/40 px-6 py-4 text-xs uppercase tracking-[0.2em] text-muted-foreground">
              <span>Название</span>
              <span>Тип</span>
              <span>Удалено</span>
              <span className="text-right">Действия</span>
            </div>

            {trashItems.length === 0 ? (
              <div className="px-6 py-16 text-center">
                <p className="text-2xl font-semibold">Корзина пуста</p>
                <p className="mt-3 text-sm leading-7 text-muted-foreground">
                  Когда появятся soft-delete endpoint-ы backend, эта страница будет получать данные из API.
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
                    {item.size ? formatBytes(item.size) : 'Folder'}
                  </p>
                </div>
                <span className="self-center text-sm text-muted-foreground">{getFileTypeLabel(item)}</span>
                <span className="self-center text-sm text-muted-foreground">{formatDate(item.deletedAt)}</span>
                <div className="flex items-center justify-end gap-2">
                  <Button onClick={() => restoreItem(item.id)} size="icon" variant="outline">
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                  <Button
                    onClick={() => {
                      if (window.confirm(`Удалить "${item.name}" безвозвратно?`)) {
                        deletePermanent(item.id)
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
