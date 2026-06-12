import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const STORAGE_KEY = 'cfs-theme-preference'
const MEDIA_QUERY = '(prefers-color-scheme: dark)'
const VALID_THEMES = new Set(['light', 'midnight', 'system'])

const ThemeContext = createContext(null)

export const themeOptions = [
  {
    value: 'light',
  },
  {
    value: 'midnight',
  },
  {
    value: 'system',
  },
]

function getSystemTheme() {
  if (typeof window === 'undefined') {
    return 'light'
  }

  return window.matchMedia(MEDIA_QUERY).matches ? 'dark' : 'light'
}

function getStoredTheme() {
  if (typeof window === 'undefined') {
    return 'system'
  }

  const storedTheme = window.localStorage.getItem(STORAGE_KEY)
  return VALID_THEMES.has(storedTheme) ? storedTheme : 'system'
}

function resolveTheme(theme) {
  return theme === 'system' ? getSystemTheme() : theme
}

function applyTheme(theme) {
  const resolvedTheme = resolveTheme(theme)

  if (typeof document === 'undefined') {
    return resolvedTheme
  }

  const root = document.documentElement

  root.classList.remove('dark', 'theme-midnight')

  if (resolvedTheme === 'dark' || resolvedTheme === 'midnight') {
    root.classList.add('dark')
  }

  if (resolvedTheme === 'midnight') {
    root.classList.add('theme-midnight')
  }

  root.dataset.theme = theme
  root.dataset.resolvedTheme = resolvedTheme
  root.style.colorScheme = resolvedTheme === 'light' ? 'light' : 'dark'

  return resolvedTheme
}

export function initializeTheme() {
  applyTheme(getStoredTheme())
}

function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(() => getStoredTheme())
  const [resolvedTheme, setResolvedTheme] = useState(() => applyTheme(getStoredTheme()))

  useEffect(() => {
    const nextResolvedTheme = applyTheme(theme)
    setResolvedTheme(nextResolvedTheme)
    window.localStorage.setItem(STORAGE_KEY, theme)
  }, [theme])

  useEffect(() => {
    const mediaQuery = window.matchMedia(MEDIA_QUERY)

    const handleSystemChange = () => {
      if (theme !== 'system') {
        return
      }

      const nextResolvedTheme = applyTheme(theme)
      setResolvedTheme(nextResolvedTheme)
    }

    mediaQuery.addEventListener('change', handleSystemChange)
    return () => mediaQuery.removeEventListener('change', handleSystemChange)
  }, [theme])

  const value = useMemo(
    () => ({
      theme,
      resolvedTheme,
      setTheme: (nextTheme) => setThemeState(VALID_THEMES.has(nextTheme) ? nextTheme : 'system'),
    }),
    [resolvedTheme, theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)

  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }

  return context
}

export default ThemeProvider
