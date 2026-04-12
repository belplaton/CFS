import axios from 'axios'

import { useAuthStore } from '@/store/auth-store'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8080/api',
  withCredentials: true,
})

client.interceptors.request.use((config) => {
  const user = useAuthStore.getState().user

  if (user?.email) {
    config.headers['X-Demo-User'] = user.email
  }

  return config
})

export default client

