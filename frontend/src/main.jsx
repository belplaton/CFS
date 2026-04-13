import React from 'react'
import ReactDOM from 'react-dom/client'
import I18nProvider from '@/components/app/I18nProvider'
import ThemeProvider, { initializeTheme } from '@/components/app/ThemeProvider'
import App from './App.jsx'
import './index.css'

initializeTheme()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <I18nProvider>
        <App />
      </I18nProvider>
    </ThemeProvider>
  </React.StrictMode>,
)
