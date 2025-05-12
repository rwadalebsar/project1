import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
// import App from './App.jsx'
import ModernApp from './ModernApp.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ModernApp />
  </StrictMode>,
)
