import React from 'react'
import ReactDOM from 'react-dom/client'
import ThemeProvider, { initializeTheme } from '@/components/app/ThemeProvider'
import App from './App.jsx'
import './index.css'

initializeTheme()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </React.StrictMode>,
)
