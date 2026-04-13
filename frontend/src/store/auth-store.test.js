import { beforeEach, describe, expect, it } from 'vitest'

import { useAuthStore } from '@/store/auth-store'

describe('auth store', () => {
  beforeEach(() => {
    window.localStorage.clear()
    useAuthStore.getState().resetAuthState()
  })

  it('requires a second factor when 2FA is enabled for the account', () => {
    useAuthStore.getState().login({ email: 'demo@cloudstorage.dev' })
    useAuthStore.getState().toggleTwoFactor()
    useAuthStore.getState().logout()

    useAuthStore.getState().login({ email: 'demo@cloudstorage.dev' })

    const stateAfterLogin = useAuthStore.getState()
    expect(stateAfterLogin.isAuthenticated).toBe(false)
    expect(stateAfterLogin.pendingTwoFactor?.email).toBe('demo@cloudstorage.dev')

    const result = useAuthStore.getState().verifyTwoFactor({ code: '246810' })

    expect(result).toEqual({ success: true, method: 'totp' })
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
    expect(useAuthStore.getState().user?.twoFactorEnabled).toBe(true)
  })

  it('accepts a backup code once and then removes it', () => {
    useAuthStore.getState().login({ email: 'demo@cloudstorage.dev' })
    useAuthStore.getState().toggleTwoFactor()

    const firstBackupCode = useAuthStore.getState().user?.backupCodes[0]

    useAuthStore.getState().logout()
    useAuthStore.getState().login({ email: 'demo@cloudstorage.dev' })

    const result = useAuthStore.getState().verifyTwoFactor({ code: firstBackupCode })

    expect(result).toEqual({ success: true, method: 'backup-code' })
    expect(useAuthStore.getState().user?.backupCodes).not.toContain(firstBackupCode)
  })
})
