import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const defaultQuotaBytes = 5 * 1024 * 1024 * 1024
const defaultTotpCode = '246810'
const storagePlanQuotas = {
  free: 5 * 1024 * 1024 * 1024,
  pro: 100 * 1024 * 1024 * 1024,
  team: 500 * 1024 * 1024 * 1024,
}

function createBackupCodes() {
  return ['AX4M-7P2Q', 'BQ8L-2V6N', 'CR3D-9K1T', 'DT5H-4W8Y', 'EU7J-6R3M', 'FX9N-5Z2P']
}

function buildUser(overrides = {}) {
  return {
    fullName: 'Platon Belyakov',
    email: 'demo@cloudstorage.dev',
    plan: 'Free',
    quotaBytes: defaultQuotaBytes,
    emailVerified: false,
    twoFactorEnabled: false,
    totpSecret: '',
    totpCode: '',
    backupCodes: [],
    ...overrides,
  }
}

function normalizeUser(user) {
  if (!user) {
    return null
  }

  return buildUser(user)
}

function normalizeProfiles(profiles) {
  if (!profiles || typeof profiles !== 'object') {
    return createProfileMap()
  }

  return Object.fromEntries(
    Object.entries(profiles).map(([email, profile]) => [email, normalizeUser(profile)]),
  )
}

function createProfileMap() {
  return {
    'demo@cloudstorage.dev': buildUser({
      email: 'demo@cloudstorage.dev',
      fullName: 'Platon Belyakov',
      emailVerified: true,
    }),
    'google.user@cloudstorage.dev': buildUser({
      fullName: 'Google User',
      email: 'google.user@cloudstorage.dev',
      emailVerified: true,
    }),
  }
}

export const useAuthStore = create(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      pendingEmail: '',
      draftUser: null,
      pendingTwoFactor: null,
      profiles: createProfileMap(),
      user: null,
      login: ({ email }) => {
        const { draftUser, profiles } = get()
        const user =
          profiles[email]
            ? { ...profiles[email] }
            : draftUser && draftUser.email === email
            ? { ...draftUser }
            : buildUser({
                email,
                fullName: email.split('@')[0].replace(/[._-]/g, ' '),
                emailVerified: email !== 'demo@cloudstorage.dev',
              })

        if (user.twoFactorEnabled) {
          set({
            isAuthenticated: false,
            pendingEmail: '',
            pendingTwoFactor: {
              email: user.email,
              fullName: user.fullName,
            },
            user: null,
          })
          return
        }

        set({
          isAuthenticated: true,
          pendingEmail: '',
          pendingTwoFactor: null,
          user,
        })
      },
      loginWithGoogle: () => {
        const googleProfile = get().profiles['google.user@cloudstorage.dev'] ?? buildUser({
          fullName: 'Google User',
          email: 'google.user@cloudstorage.dev',
          emailVerified: true,
        })

        if (googleProfile.twoFactorEnabled) {
          set({
            isAuthenticated: false,
            pendingEmail: '',
            pendingTwoFactor: {
              email: googleProfile.email,
              fullName: googleProfile.fullName,
            },
            user: null,
          })
          return
        }

        set({
          isAuthenticated: true,
          pendingEmail: '',
          pendingTwoFactor: null,
          user: googleProfile,
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
          pendingTwoFactor: null,
        })
      },
      verifyEmail: () => {
        const { draftUser, profiles, user } = get()

        if (user) {
          set({
            user: {
              ...user,
              emailVerified: true,
            },
            profiles: {
              ...profiles,
              [user.email]: {
                ...user,
                emailVerified: true,
              },
            },
            pendingEmail: '',
          })
          return
        }

        if (draftUser) {
          const nextDraftUser = {
            ...draftUser,
            emailVerified: true,
          }

          set({
            draftUser: nextDraftUser,
            profiles: {
              ...profiles,
              [nextDraftUser.email]: nextDraftUser,
            },
            pendingEmail: '',
          })
        }
      },
      verifyTwoFactor: ({ code }) => {
        const { pendingTwoFactor, profiles } = get()

        if (!pendingTwoFactor) {
          return { success: false, reason: 'missing-challenge' }
        }

        const user = profiles[pendingTwoFactor.email]

        if (!user) {
          return { success: false, reason: 'unknown-user' }
        }

        const normalizedCode = code.toString().trim().toUpperCase()
        const isPrimaryCodeValid = normalizedCode === (user.totpCode || defaultTotpCode)
        const backupCodes = user.backupCodes ?? []
        const isBackupCodeValid = backupCodes.includes(normalizedCode)

        if (!isPrimaryCodeValid && !isBackupCodeValid) {
          return { success: false, reason: 'invalid-code' }
        }

        const nextUser = {
          ...user,
          backupCodes: isBackupCodeValid
            ? backupCodes.filter((backupCode) => backupCode !== normalizedCode)
            : backupCodes,
        }

        set({
          isAuthenticated: true,
          pendingTwoFactor: null,
          profiles: {
            ...profiles,
            [nextUser.email]: nextUser,
          },
          user: nextUser,
        })

        return {
          success: true,
          method: isBackupCodeValid ? 'backup-code' : 'totp',
        }
      },
      cancelTwoFactor: () => {
        set({
          pendingTwoFactor: null,
        })
      },
      toggleTwoFactor: () => {
        const { profiles, user } = get()
        if (!user) {
          return
        }

        const isEnabling = !user.twoFactorEnabled
        const nextUser = {
          ...user,
          twoFactorEnabled: isEnabling,
          totpSecret: isEnabling ? 'JBSW-Y3DP-EHPK-3PXP' : '',
          totpCode: isEnabling ? defaultTotpCode : '',
          backupCodes: isEnabling ? createBackupCodes() : [],
        }

        set({
          user: nextUser,
          profiles: {
            ...profiles,
            [nextUser.email]: nextUser,
          },
        })
      },
      setStoragePlan: ({ plan }) => {
        const { user, profiles } = get()
        if (!user) {
          return
        }

        const normalizedPlan = (plan ?? 'free').toString().trim().toLowerCase()
        const quotaBytes = storagePlanQuotas[normalizedPlan] ?? storagePlanQuotas.free
        const nextUser = {
          ...user,
          plan: normalizedPlan.charAt(0).toUpperCase() + normalizedPlan.slice(1),
          quotaBytes,
        }

        set({
          user: nextUser,
          profiles: {
            ...profiles,
            [nextUser.email]: nextUser,
          },
        })
      },
      logout: () => {
        set({
          isAuthenticated: false,
          pendingTwoFactor: null,
          user: null,
        })
      },
      resetAuthState: () =>
        set({
          isAuthenticated: false,
          pendingEmail: '',
          draftUser: null,
          pendingTwoFactor: null,
          profiles: createProfileMap(),
          user: null,
        }),
    }),
    {
      name: 'cfs-auth-store',
      merge: (persistedState, currentState) => {
        const nextState = persistedState ?? {}

        return {
          ...currentState,
          ...nextState,
          draftUser: normalizeUser(nextState.draftUser),
          profiles: normalizeProfiles(nextState.profiles),
          user: normalizeUser(nextState.user),
        }
      },
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        pendingEmail: state.pendingEmail,
        draftUser: state.draftUser,
        pendingTwoFactor: state.pendingTwoFactor,
        profiles: state.profiles,
        user: state.user,
      }),
    },
  ),
)

