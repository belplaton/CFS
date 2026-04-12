import { RotateCcw, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { formatBytes, formatDate, getFileTypeLabel } from '@/lib/utils'
import { useFileStore } from '@/store/file-store'

function TrashPage() {
  const { deletePermanent, emptyTrash, items, restoreItem } = useFileStore((state) => state)
  const trashItems = items.filter((item) => item.deletedAt)

  return (
    <div className="space-y-6">
      <section className="rounded-[32px] border border-slate-200 bg-white p-6 shadow-[0_15px_40px_rgba(148,163,184,0.12)] md:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-rose-700">Trash</p>
            <h1 className="mt-3 text-3xl font-semibold">Корзина</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600">
              Отдельная страница корзины закрывает спринт 5 по roadmap. Восстановление и
              безвозвратное удаление уже отрисованы на уровне интерфейса и store.
            </p>
          </div>
          <Button
            className="gap-2 rounded-full"
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

      <section className="overflow-hidden rounded-[32px] border border-slate-200 bg-white shadow-[0_15px_40px_rgba(148,163,184,0.12)]">
        <div className="overflow-x-auto">
          <div className="min-w-[820px]">
            <div className="grid grid-cols-[minmax(0,1.8fr)_140px_150px_170px] gap-4 border-b border-slate-200 px-6 py-4 text-xs uppercase tracking-[0.25em] text-slate-500">
              <span>Название</span>
              <span>Тип</span>
              <span>Удалено</span>
              <span className="text-right">Действия</span>
            </div>

            {trashItems.length === 0 ? (
              <div className="px-6 py-16 text-center">
                <p className="text-2xl font-semibold">Корзина пуста</p>
                <p className="mt-3 text-sm leading-7 text-slate-600">
                  Когда появятся soft-delete endpoint-ы backend, эта страница будет получать данные из API.
                </p>
              </div>
            ) : null}

            {trashItems.map((item) => (
              <div
                className="grid grid-cols-[minmax(0,1.8fr)_140px_150px_170px] gap-4 border-b border-slate-100 px-6 py-4 last:border-b-0"
                key={item.id}
              >
                <div className="min-w-0">
                  <p className="truncate font-medium">{item.name}</p>
                  <p className="text-sm text-slate-500">
                    {item.size ? formatBytes(item.size) : 'Folder'}
                  </p>
                </div>
                <span className="self-center text-sm text-slate-600">{getFileTypeLabel(item)}</span>
                <span className="self-center text-sm text-slate-600">{formatDate(item.deletedAt)}</span>
                <div className="flex items-center justify-end gap-2">
                  <Button className="rounded-full" onClick={() => restoreItem(item.id)} size="icon" variant="outline">
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                  <Button
                    className="rounded-full text-rose-600"
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
