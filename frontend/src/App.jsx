import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import AppShell from '@/components/app/AppShell'
import ProtectedRoute from '@/components/app/ProtectedRoute'
import FilesPage from '@/pages/FilesPage'
import ForgotPasswordPage from '@/pages/ForgotPasswordPage'
import LandingPage from '@/pages/LandingPage'
import LoginPage from '@/pages/LoginPage'
import NotFoundPage from '@/pages/NotFoundPage'
import RegisterPage from '@/pages/RegisterPage'
import ResetPasswordPage from '@/pages/ResetPasswordPage'
import SecurityPage from '@/pages/SecurityPage'
import TrashPage from '@/pages/TrashPage'
import VerifyEmailPage from '@/pages/VerifyEmailPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<LandingPage />} path="/" />
        <Route element={<LoginPage />} path="/login" />
        <Route element={<RegisterPage />} path="/register" />
        <Route element={<ForgotPasswordPage />} path="/forgot-password" />
        <Route element={<ResetPasswordPage />} path="/reset-password" />
        <Route element={<VerifyEmailPage />} path="/verify-email" />

        <Route element={<ProtectedRoute />} path="/app">
          <Route element={<AppShell />}>
            <Route element={<Navigate replace to="/app/files" />} index />
            <Route element={<FilesPage />} path="files" />
            <Route element={<TrashPage />} path="trash" />
            <Route element={<SecurityPage />} path="security" />
          </Route>
        </Route>

        <Route element={<NotFoundPage />} path="*" />
      </Routes>
    </BrowserRouter>
  )
}

export default App
