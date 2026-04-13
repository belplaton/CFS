import { createContext, useContext, useEffect, useMemo, useState } from 'react'

import {
  getAvailableLanguages,
  getLanguage,
  setLanguage as setManagerLanguage,
  subscribeToLanguage,
  t as translate,
} from '@/i18n/manager'

const I18nContext = createContext({
  availableLanguages: getAvailableLanguages(),
  language: getLanguage(),
  setLanguage: setManagerLanguage,
  t: (key, variables) => translate(key, variables),
})

function I18nProvider({ children }) {
  const [language, setLanguageState] = useState(getLanguage)

  useEffect(() => subscribeToLanguage(setLanguageState), [])

  const value = useMemo(
    () => ({
      availableLanguages: getAvailableLanguages(),
      language,
      setLanguage: setManagerLanguage,
      t: (key, variables) => translate(key, variables, language),
    }),
    [language],
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  return useContext(I18nContext)
}

export default I18nProvider
