import { beforeEach, describe, expect, it } from 'vitest'

import { useAuthStore } from '@/store/auth-store'

describe('auth store', () => {
  beforeEach(() => {
    window.localStorage.clear()
    useAuthStore.getState().resetAuthState()
  })

  it('clears session state on logout', async () => {
    useAuthStore.setState({
      isAuthenticated: true,
      accessToken: 'token',
      refreshToken: 'refresh',
      user: { email: 'user@example.com' },
    })

    await useAuthStore.getState().logout()

    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(useAuthStore.getState().accessToken).toBeNull()
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('resets state to initial values', () => {
    useAuthStore.setState({
      isAuthenticated: true,
      error: 'bad',
      user: { email: 'user@example.com' },
    })

    useAuthStore.getState().resetAuthState()

    expect(useAuthStore.getState().error).toBeNull()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })
})
