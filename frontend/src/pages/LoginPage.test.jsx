import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'

import ThemeProvider from '@/components/app/ThemeProvider'
import LoginPage from '@/pages/LoginPage'
import { useAuthStore } from '@/store/auth-store'

describe('LoginPage', () => {
  beforeEach(() => {
    window.localStorage.clear()
    useAuthStore.getState().resetAuthState()
    useAuthStore.getState().login({ email: 'demo@cloudstorage.dev' })
    useAuthStore.getState().toggleTwoFactor()
    useAuthStore.getState().logout()
    useAuthStore.getState().login({ email: 'demo@cloudstorage.dev' })
  })

  it('renders the two-factor step and completes login after a valid code', async () => {
    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route element={<LoginPage />} path="/login" />
            <Route element={<div>files page</div>} path="/app/files" />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>,
    )

    expect(screen.getByText(/Для аккаунта/i)).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText(/Код подтверждения/i), {
      target: { value: '246810' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Подтвердить вход/i }))

    expect(await screen.findByText('files page')).toBeInTheDocument()
  })
})
