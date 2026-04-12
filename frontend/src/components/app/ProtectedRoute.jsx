import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuthStore } from '@/store/auth-store'

function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate replace state={{ from: location }} to="/login" />
  }

  return <Outlet />
}

export default ProtectedRoute

