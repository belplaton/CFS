import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import client from '@/api/client'
import { useFileStore } from '@/store/file-store'

function derivePlan(storageQuota = 0) {
  if (storageQuota >= 500 * 1024 * 1024 * 1024) {
    return 'Team'
  }
  if (storageQuota > 5 * 1024 * 1024 * 1024) {
    return 'Pro'
  }
  return 'Free'
}

function normalizeUser(user) {
  if (!user) {
    return null
  }

  return {
    ...user,
    emailVerified: Boolean(user.is_verified),
    quotaBytes: user.storage_quota ?? 0,
    usedBytes: user.used_storage ?? 0,
    plan: derivePlan(user.storage_quota ?? 0),
  }
}

const initialState = {
  isAuthenticated: false,
  user: null,
  accessToken: null,
  refreshToken: null,
  hasHydrated: false,
  isLoading: false,
  error: null,
}

export const useAuthStore = create(
  persist(
    (set, get) => ({
      ...initialState,

      register: async (email, password, fullName) => {
        set({ isLoading: true, error: null })
        try {
          const response = await client.post('/auth/register', {
            email,
            password,
            full_name: fullName || null,
          })
          const { access_token, refresh_token } = response.data

          set({
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            hasHydrated: true,
          })

          await get().refreshProfile()
          set({ isLoading: false })
          return { success: true }
        } catch (error) {
          const detail = error.response?.data?.detail
          const message = typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((d) => d.msg || d.message || String(d)).join('; ')
              : 'Registration failed'
          set({ isLoading: false, error: message })
          return { success: false, error: message }
        }
      },

      login: async (email, password) => {
        set({ isLoading: true, error: null })
        try {
          const response = await client.post('/auth/login', {
            email,
            password,
          })
          const { access_token, refresh_token } = response.data

          set({
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            hasHydrated: true,
          })

          await get().refreshProfile()
          set({ isLoading: false })
          return { success: true }
        } catch (error) {
          const detail = error.response?.data?.detail
          const message = typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
              ? detail.map((d) => d.msg || d.message || String(d)).join('; ')
              : 'Login failed'
          set({ isLoading: false, error: message })
          return { success: false, error: message }
        }
      },

      refreshProfile: async () => {
        if (!get().accessToken) {
          return null
        }

        try {
          const response = await client.get('/auth/me')
          const user = normalizeUser(response.data)
          set({ user, isAuthenticated: true, error: null })
          return user
        } catch (error) {
          useFileStore.getState().resetData()
          set({
            ...initialState,
            hasHydrated: true,
            error: error.response?.data?.detail || 'Session expired',
          })
          return null
        }
      },

      clearError: () => set({ error: null }),

      setTokens: ({ accessToken, refreshToken }) => {
        set({
          accessToken,
          refreshToken,
          isAuthenticated: Boolean(accessToken),
          hasHydrated: true,
        })
      },

      requestEmailVerification: async () => {
        try {
          const response = await client.post('/auth/verify-email/request')
          return {
            success: true,
            actionUrl: response.data?.action_url ?? null,
            token: response.data?.token ?? null,
            message: response.data?.message ?? null,
          }
        } catch (error) {
          const message = error.response?.data?.detail || 'Unable to start email verification'
          set({ error: message })
          return { success: false, error: message }
        }
      },

      switchPlan: async (plan) => {
        set({ isLoading: true, error: null })
        try {
          const response = await client.post('/auth/plan', { plan })
          const user = normalizeUser(response.data)
          useFileStore.setState({
            quota: {
              used: user.usedBytes ?? 0,
              total: user.quotaBytes ?? 0,
              percent: Math.round(((user.usedBytes ?? 0) / Math.max(user.quotaBytes ?? 1, 1)) * 1000) / 10,
            },
          })
          set({ user, isAuthenticated: true, isLoading: false, error: null })
          return { success: true, user }
        } catch (error) {
          const message = error.response?.data?.detail || 'Unable to change plan'
          set({ isLoading: false, error: message })
          return { success: false, error: message }
        }
      },

      verifyEmailToken: async (token) => {
        set({ isLoading: true, error: null })
        try {
          const response = await client.get('/auth/verify-email', {
            params: { token },
          })
          const user = await get().refreshProfile()
          set({ isLoading: false })
          return { success: true, data: response.data, user }
        } catch (error) {
          const message = error.response?.data?.detail || 'Unable to verify email'
          set({ isLoading: false, error: message })
          return { success: false, error: message }
        }
      },

      resetPassword: async ({ token, password }) => {
        set({ isLoading: true, error: null })
        try {
          const response = await client.post('/auth/reset-password', {
            token,
            new_password: password,
          })
          set({ isLoading: false })
          return { success: true, message: response.data?.message || 'Password updated successfully' }
        } catch (error) {
          const message = error.response?.data?.detail || 'Unable to reset password'
          set({ isLoading: false, error: message })
          return { success: false, error: message }
        }
      },

      logout: async () => {
        const refreshToken = get().refreshToken
        if (refreshToken) {
          try {
            await client.post('/auth/logout', { refresh_token: refreshToken })
          } catch {
            // Local logout still wins even if the revoke call fails.
          }
        }
        useFileStore.getState().resetData()
        set({ ...initialState, hasHydrated: true })
      },

      resetAuthState: () => {
        useFileStore.getState().resetData()
        set({ ...initialState, hasHydrated: true })
      },
    }),
    {
      name: 'cfs-auth-store',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setTokens({
          accessToken: state.accessToken,
          refreshToken: state.refreshToken,
        })
        useAuthStore.setState({ hasHydrated: true })
      },
    },
  ),
)
