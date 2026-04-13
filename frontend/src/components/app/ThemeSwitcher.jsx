import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import { Check, Laptop, MoonStar, Palette, SunMedium } from 'lucide-react'

import { useI18n } from '@/components/app/I18nProvider'
import { themeOptions, useTheme } from '@/components/app/ThemeProvider'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

function getThemeIcon(resolvedTheme, selectedTheme) {
  if (selectedTheme === 'system') {
    return Laptop
  }

  if (resolvedTheme === 'midnight') {
    return Palette
  }

  if (resolvedTheme === 'dark') {
    return MoonStar
  }

  return SunMedium
}

function ThemeSwitcher({ align = 'end', compact = false }) {
  const { resolvedTheme, setTheme, theme } = useTheme()
  const { t } = useI18n()
  const Icon = getThemeIcon(resolvedTheme, theme)

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button
          aria-label={t('theme.title')}
          className={cn(compact ? 'h-10 w-10 px-0' : 'h-10 w-10 px-0')}
          size="icon"
          variant="outline"
        >
          <Icon className="h-4 w-4" />
        </Button>
      </DropdownMenu.Trigger>

      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align={align}
          className="z-50 max-h-[300px] min-w-[260px] overflow-y-auto rounded-xl border bg-popover p-2 shadow-xl"
          sideOffset={10}
        >
          <div className="px-3 py-2">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{t('theme.title')}</p>
            <p className="mt-2 text-sm font-medium">{t('theme.subtitle')}</p>
          </div>

          <div className="mt-1 space-y-1">
            {themeOptions.map((option) => {
              const isSelected = option.value === theme

              return (
                <DropdownMenu.Item
                  className="flex cursor-pointer items-start justify-between gap-3 rounded-lg px-3 py-2.5 outline-none transition hover:bg-muted focus:bg-muted"
                  key={option.value}
                  onSelect={() => setTheme(option.value)}
                >
                  <div>
                    <p className="text-sm font-medium">{t(`theme.options.${option.value}.label`)}</p>
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">
                      {t(`theme.options.${option.value}.description`)}
                    </p>
                  </div>
                  <div className="pt-0.5">
                    {isSelected ? <Check className="h-4 w-4 text-foreground" /> : null}
                  </div>
                </DropdownMenu.Item>
              )
            })}
          </div>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}

export default ThemeSwitcher
