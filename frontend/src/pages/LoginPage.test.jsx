import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'

import I18nProvider from '@/components/app/I18nProvider'
import ThemeProvider from '@/components/app/ThemeProvider'
import { setLanguage } from '@/i18n/manager'
import LoginPage from '@/pages/LoginPage'
import { useAuthStore } from '@/store/auth-store'

describe('LoginPage', () => {
  beforeEach(() => {
    window.localStorage.clear()
    setLanguage('en')
    useAuthStore.getState().resetAuthState()
  })

  it('renders the standard login form', () => {
    render(
      <ThemeProvider>
        <I18nProvider>
          <MemoryRouter initialEntries={['/login']}>
            <Routes>
              <Route element={<LoginPage />} path="/login" />
            </Routes>
          </MemoryRouter>
        </I18nProvider>
      </ThemeProvider>,
    )

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })
})
