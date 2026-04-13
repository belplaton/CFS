import { useRef, useState } from 'react'
import { FolderPlus, UploadCloud } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

function UploadDropzone({ compact = false, onCreateFolder, onFilesSelected }) {
  const inputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFiles = (fileList) => {
    const files = Array.from(fileList ?? [])
    if (files.length === 0) {
      return
    }

    onFilesSelected(files)
  }

  return (
    <div
      className={cn(
        'rounded-xl border border-dashed transition-colors',
        compact ? 'p-5' : 'p-6 md:p-8',
        isDragging
          ? 'border-primary bg-muted'
          : 'border-border bg-background',
      )}
      onDragEnter={(event) => {
        event.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={(event) => {
        event.preventDefault()
        setIsDragging(false)
      }}
      onDragOver={(event) => {
        event.preventDefault()
      }}
      onDrop={(event) => {
        event.preventDefault()
        setIsDragging(false)
        handleFiles(event.dataTransfer.files)
      }}
    >
      <div className={cn('flex flex-col gap-6', compact ? '' : 'lg:flex-row lg:items-center lg:justify-between')}>
        <div className="max-w-2xl">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg border bg-muted">
            <UploadCloud className="h-5 w-5" />
          </div>
          <h2 className={cn('font-semibold', compact ? 'mt-4 text-lg' : 'mt-5 text-2xl')}>Загрузка и структура данных</h2>
          <p className={cn('mt-3 text-muted-foreground', compact ? 'text-sm leading-6' : 'text-sm leading-7 md:text-base')}>
            {compact
              ? 'Быстрый доступ к загрузке файлов и созданию папок внутри текущего раздела.'
              : 'Компонент уже покрывает drag & drop, создание папок и локальное обновление состояния. Когда backend будет готов, сюда можно подключить upload endpoint и прогресс по Axios.'}
          </p>
        </div>

        <div className={cn('flex gap-3', compact ? 'flex-col' : 'flex-wrap')}>
          <input
            id="file-upload-trigger"
            className="hidden"
            multiple
            onChange={(event) => handleFiles(event.target.files)}
            ref={inputRef}
            type="file"
          />
          <Button className={cn('gap-2 px-6', compact && 'w-full justify-center')} onClick={() => inputRef.current?.click()}>
            <UploadCloud className="h-4 w-4" />
            Выбрать файлы
          </Button>
          <Button className={cn('gap-2 px-6', compact && 'w-full justify-center')} onClick={onCreateFolder} variant="outline">
            <FolderPlus className="h-4 w-4" />
            Создать папку
          </Button>
        </div>
      </div>
    </div>
  )
}

export default UploadDropzone

