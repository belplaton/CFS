import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import { Eye, FolderOpen, MoreHorizontal, Pencil, Trash2, Workflow } from 'lucide-react'

import { useI18n } from '@/components/app/I18nProvider'
import { Button } from '@/components/ui/button'

function ItemActionsMenu({ item, onMove, onOpen, onPreview, onRename, onTrash }) {
  const { t } = useI18n()

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button size="icon" variant="ghost">
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          className="z-50 min-w-[220px] rounded-xl border bg-background p-2 shadow-xl"
          sideOffset={10}
        >
          {item.kind === 'folder' ? (
            <DropdownMenu.Item
              className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm outline-none transition hover:bg-muted focus:bg-muted"
              onSelect={onOpen}
            >
              <FolderOpen className="h-4 w-4 text-foreground" />
              {t('itemMenu.openFolder')}
            </DropdownMenu.Item>
          ) : (
            <DropdownMenu.Item
              className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm outline-none transition hover:bg-muted focus:bg-muted"
              onSelect={onPreview}
            >
              <Eye className="h-4 w-4 text-foreground" />
              {t('itemMenu.openPreview')}
            </DropdownMenu.Item>
          )}

          <DropdownMenu.Item
            className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm outline-none transition hover:bg-muted focus:bg-muted"
            onSelect={onRename}
          >
            <Pencil className="h-4 w-4 text-foreground" />
            {t('itemMenu.rename')}
          </DropdownMenu.Item>

          <DropdownMenu.Item
            className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm outline-none transition hover:bg-muted focus:bg-muted"
            onSelect={onMove}
          >
            <Workflow className="h-4 w-4 text-foreground" />
            {t('itemMenu.move')}
          </DropdownMenu.Item>

          <DropdownMenu.Separator className="my-2 h-px bg-border" />

          <DropdownMenu.Item
            className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm text-destructive outline-none transition hover:bg-destructive/10 focus:bg-destructive/10"
            onSelect={onTrash}
          >
            <Trash2 className="h-4 w-4" />
            {t('itemMenu.toTrash')}
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}

export default ItemActionsMenu
