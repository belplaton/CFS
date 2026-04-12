import { useRef, useState } from 'react'
import { FolderPlus, UploadCloud } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

function UploadDropzone({ onCreateFolder, onFilesSelected }) {
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
        'rounded-[28px] border border-dashed p-6 transition md:p-8',
        isDragging
          ? 'border-sky-500 bg-sky-50'
          : 'border-slate-300 bg-[linear-gradient(180deg,_rgba(255,255,255,0.96),_rgba(241,245,249,0.92))]',
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
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="max-w-2xl">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-950 text-white">
            <UploadCloud className="h-6 w-6" />
          </div>
          <h2 className="mt-5 text-2xl font-semibold">Загрузка и структура данных</h2>
          <p className="mt-3 text-sm leading-7 text-slate-600 md:text-base">
            Компонент уже покрывает drag & drop, создание папок и локальное обновление состояния.
            Когда backend будет готов, сюда можно подключить upload endpoint и прогресс по Axios.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <input
            className="hidden"
            multiple
            onChange={(event) => handleFiles(event.target.files)}
            ref={inputRef}
            type="file"
          />
          <Button className="gap-2 rounded-full px-6" onClick={() => inputRef.current?.click()}>
            <UploadCloud className="h-4 w-4" />
            Выбрать файлы
          </Button>
          <Button className="gap-2 rounded-full px-6" onClick={onCreateFolder} variant="outline">
            <FolderPlus className="h-4 w-4" />
            Создать папку
          </Button>
        </div>
      </div>
    </div>
  )
}

export default UploadDropzone

