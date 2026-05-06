import { create } from "zustand";
import { persist } from "zustand/middleware";
import client from "@/api/client";

export const useAuthStore = create(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false,
      error: null,

      // Registration
      register: async (email, password, fullName) => {
        set({ isLoading: true, error: null });
        try {
          const response = await client.post("/auth/register", {
            email,
            password,
            full_name: fullName,
          });

          // Backend returns tokens and user info
          const { access_token, refresh_token } = response.data;

          // Since email verification is disabled, user is active immediately
          // Fetch user data to get full profile
          const userResponse = await client.get("/auth/me", {
            headers: { Authorization: `Bearer ${access_token}` },
          });

          set({
            isAuthenticated: true,
            user: userResponse.data,
            accessToken: access_token,
            refreshToken: refresh_token,
            isLoading: false,
          });

          return { success: true };
        } catch (error) {
          const message = error.response?.data?.detail || "Registration failed";
          set({ isLoading: false, error: message });
          return { success: false, error: message };
        }
      },

      // Login
      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const response = await client.post("/auth/login", {
            email,
            password,
          });

          const { access_token, refresh_token } = response.data;

          // Fetch user data
          const userResponse = await client.get("/auth/me", {
            headers: { Authorization: `Bearer ${access_token}` },
          });

          set({
            isAuthenticated: true,
            user: userResponse.data,
            accessToken: access_token,
            refreshToken: refresh_token,
            isLoading: false,
          });

          return { success: true };
        } catch (error) {
          const message = error.response?.data?.detail || "Login failed";
          set({ isLoading: false, error: message });
          return { success: false, error: message };
        }
      },

      // Logout
      logout: () => {
        set({
          isAuthenticated: false,
          user: null,
          accessToken: null,
          refreshToken: null,
          error: null,
        });
      },

      // Clear error
      clearError: () => set({ error: null }),

      // TODO: Implement Google OAuth, 2FA, etc.
    }),
    {
      name: "cfs-auth-store",
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
