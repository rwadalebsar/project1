import { StrictMode, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import './modern.css'
import './i18n' // Import i18n configuration
import ModernApp from './ModernApp.jsx'
import Login from './components/auth/Login.jsx'
import Register from './components/auth/Register.jsx'
import ProtectedRoute from './components/auth/ProtectedRoute.jsx'
import SubscriptionPage from './components/subscription/SubscriptionPage.jsx'
import { AuthProvider } from './context/AuthContext.jsx'

const App = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <ModernApp />
              </ProtectedRoute>
            }
          />

          {/* Subscription routes */}
          <Route
            path="/subscription"
            element={
              <ProtectedRoute>
                <SubscriptionPage />
              </ProtectedRoute>
            }
          />

          {/* Anomaly detection requires basic subscription */}
          <Route
            path="/anomalies"
            element={
              <ProtectedRoute requiredSubscription="basic">
                <ModernApp initialTab="anomalies" />
              </ProtectedRoute>
            }
          />

          {/* Redirect root to dashboard or login */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Suspense fallback={<div>Loading...</div>}>
      <App />
    </Suspense>
  </StrictMode>,
)
