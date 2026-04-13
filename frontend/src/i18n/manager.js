const STORAGE_KEY = 'cfs-language-preference'
const DEFAULT_LANGUAGE = 'en'

const localeModules = import.meta.glob('../locales/*.json', { eager: true, import: 'default' })

const dictionaries = Object.fromEntries(
  Object.entries(localeModules).map(([path, content]) => {
    const fileName = path.split('/').pop() ?? ''
    const language = fileName.replace('.json', '').toLowerCase()
    return [language, content]
  }),
)

const availableLanguages = Object.keys(dictionaries)

function normalizeLanguage(language) {
  return language?.toString().trim().toLowerCase() ?? ''
}

function matchLanguage(candidate) {
  const normalized = normalizeLanguage(candidate)
  if (!normalized) {
    return null
  }

  if (availableLanguages.includes(normalized)) {
    return normalized
  }

  const base = normalized.split('-')[0]
  if (availableLanguages.includes(base)) {
    return base
  }

  return null
}

function readStoredLanguage() {
  if (typeof window === 'undefined') {
    return null
  }

  return window.localStorage.getItem(STORAGE_KEY)
}

function resolveStartupLanguage() {
  const stored = matchLanguage(readStoredLanguage())
  if (stored) {
    return stored
  }

  return DEFAULT_LANGUAGE
}

let currentLanguage = resolveStartupLanguage()

const subscribers = new Set()

function notify() {
  subscribers.forEach((listener) => listener(currentLanguage))
}

function deepGet(object, dottedKey) {
  return dottedKey.split('.').reduce((accumulator, key) => {
    if (accumulator && typeof accumulator === 'object' && key in accumulator) {
      return accumulator[key]
    }

    return undefined
  }, object)
}

function interpolate(template, variables = {}) {
  if (typeof template !== 'string') {
    return template
  }

  return template.replace(/\{(\w+)\}/g, (_, key) => {
    const value = variables[key]
    return value === undefined || value === null ? `{${key}}` : String(value)
  })
}

export function getAvailableLanguages() {
  return [...availableLanguages]
}

export function getLanguage() {
  return currentLanguage
}

export function setLanguage(language) {
  const nextLanguage = matchLanguage(language) ?? DEFAULT_LANGUAGE
  if (nextLanguage === currentLanguage) {
    return nextLanguage
  }

  currentLanguage = nextLanguage

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, nextLanguage)
  }

  notify()
  return nextLanguage
}

export function subscribeToLanguage(listener) {
  subscribers.add(listener)
  return () => subscribers.delete(listener)
}

export function t(key, variables = {}, language = currentLanguage) {
  const selectedLanguage = matchLanguage(language) ?? DEFAULT_LANGUAGE
  const selectedDictionary = dictionaries[selectedLanguage] ?? {}
  const fallbackDictionary = dictionaries[DEFAULT_LANGUAGE] ?? {}

  const selectedValue = deepGet(selectedDictionary, key)
  if (typeof selectedValue === 'string') {
    return interpolate(selectedValue, variables)
  }

  const fallbackValue = deepGet(fallbackDictionary, key)
  if (typeof fallbackValue === 'string') {
    return interpolate(fallbackValue, variables)
  }

  return key
}

export function getDateLocale(language = currentLanguage) {
  const normalized = matchLanguage(language) ?? DEFAULT_LANGUAGE
  return normalized === 'ru' ? 'ru-RU' : 'en-US'
}
