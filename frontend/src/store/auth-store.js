import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const defaultQuotaBytes = 5 * 1024 * 1024 * 1024

function buildUser(overrides = {}) {
  return {
    fullName: 'Platon Belyakov',
    email: 'demo@cloudstorage.dev',
    plan: 'Free',
    quotaBytes: defaultQuotaBytes,
    emailVerified: false,
    twoFactorEnabled: false,
    ...overrides,
  }
}

export const useAuthStore = create(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      pendingEmail: '',
      draftUser: null,
      user: null,
      login: ({ email }) => {
        const draftUser = get().draftUser
        const user =
          draftUser && draftUser.email === email
            ? { ...draftUser }
            : buildUser({
                email,
                fullName: email.split('@')[0].replace(/[._-]/g, ' '),
                emailVerified: email !== 'demo@cloudstorage.dev',
              })

        set({
          isAuthenticated: true,
          pendingEmail: '',
          user,
        })
      },
      loginWithGoogle: () => {
        set({
          isAuthenticated: true,
          pendingEmail: '',
          user: buildUser({
            fullName: 'Google User',
            email: 'google.user@cloudstorage.dev',
            emailVerified: true,
          }),
        })
      },
      register: ({ fullName, email }) => {
        const draftUser = buildUser({
          fullName,
          email,
          emailVerified: false,
        })

        set({
          isAuthenticated: false,
          pendingEmail: email,
          draftUser,
        })
      },
      verifyEmail: () => {
        const { draftUser, user } = get()

        if (user) {
          set({
            user: {
              ...user,
              emailVerified: true,
            },
            pendingEmail: '',
          })
          return
        }

        if (draftUser) {
          set({
            draftUser: {
              ...draftUser,
              emailVerified: true,
            },
            pendingEmail: '',
          })
        }
      },
      toggleTwoFactor: () => {
        const user = get().user
        if (!user) {
          return
        }

        set({
          user: {
            ...user,
            twoFactorEnabled: !user.twoFactorEnabled,
          },
        })
      },
      logout: () => {
        set({
          isAuthenticated: false,
          user: null,
        })
      },
    }),
    {
      name: 'cfs-auth-store',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        pendingEmail: state.pendingEmail,
        draftUser: state.draftUser,
        user: state.user,
      }),
    },
  ),
)

