import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import { Check, Languages } from 'lucide-react'

import { useI18n } from '@/components/app/I18nProvider'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

function LanguageSwitcher({ align = 'end', compact = false }) {
  const { availableLanguages, language, setLanguage, t } = useI18n()

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button
          aria-label={t('language.label')}
          className={cn(compact ? 'h-10 w-10 px-0' : 'h-10 w-10 px-0')}
          size="icon"
          variant="outline"
        >
          <Languages className="h-4 w-4" />
        </Button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align={align}
          className="z-50 max-h-[220px] min-w-[220px] overflow-y-auto rounded-xl border bg-popover p-2 shadow-xl"
          sideOffset={10}
        >
          <div className="px-3 py-2">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{t('language.label')}</p>
          </div>
          <div className="mt-1 space-y-1">
            {availableLanguages.map((lang) => {
              const isSelected = lang === language
              return (
                <DropdownMenu.Item
                  className="flex cursor-pointer items-center justify-between rounded-lg px-3 py-2 outline-none transition hover:bg-muted focus:bg-muted"
                  key={lang}
                  onSelect={() => setLanguage(lang)}
                >
                  <span className="text-sm font-medium">{t(`language.${lang}`)}</span>
                  {isSelected ? <Check className="h-4 w-4 text-foreground" /> : null}
                </DropdownMenu.Item>
              )
            })}
          </div>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}

export default LanguageSwitcher
