import axios from "axios";

import { useAuthStore } from "@/store/auth-store";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8080/api",
  withCredentials: true, // Important for CORS with credentials
});

// Request interceptor to add Authorization header
client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// Response interceptor for token refresh (optional, for later)
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Handle 401 Unauthorized - maybe trigger refresh token logic here
    return Promise.reject(error);
  },
);

export default client;
