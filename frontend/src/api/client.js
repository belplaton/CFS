import axios from "axios";

import { useAuthStore } from "@/store/auth-store";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8080/api",
  withCredentials: true, // Important for CORS with credentials
});

let refreshPromise = null;

// Request interceptor to add Authorization header
client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;

  if (token && !config.headers?.Authorization) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// Response interceptor for token refresh (optional, for later)
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;
    const store = useAuthStore.getState();

    if (
      status === 401
      && store.refreshToken
      && !originalRequest?._retry
      && !String(originalRequest?.url ?? "").includes("/auth/refresh")
      && !String(originalRequest?.url ?? "").includes("/auth/login")
      && !String(originalRequest?.url ?? "").includes("/auth/register")
      && !String(originalRequest?.url ?? "").includes("/auth/logout")
    ) {
      originalRequest._retry = true;

      try {
        if (!refreshPromise) {
          refreshPromise = client.post(
            "/auth/refresh",
            null,
            {
              headers: {
                Authorization: `Bearer ${store.refreshToken}`,
              },
            },
          ).finally(() => {
            refreshPromise = null;
          });
        }

        const refreshResponse = await refreshPromise;
        useAuthStore.getState().setTokens({
          accessToken: refreshResponse.data.access_token,
          refreshToken: refreshResponse.data.refresh_token,
        });

        originalRequest.headers = originalRequest.headers ?? {};
        originalRequest.headers.Authorization = `Bearer ${refreshResponse.data.access_token}`;
        return client(originalRequest);
      } catch (refreshError) {
        useAuthStore.getState().resetAuthState();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

export default client;
