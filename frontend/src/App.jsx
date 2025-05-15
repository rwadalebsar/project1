import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { AuthProvider } from './context/AuthContext'
import { I18nextProvider } from 'react-i18next'
import i18n from './i18n'
import './App.css'

// Components
import Layout from './components/common/Layout'
import Dashboard from './components/dashboard/Dashboard'
import EnterprisePage from './components/enterprise/EnterprisePage'
import Login from './components/auth/Login'
import Register from './components/auth/Register'
import ProtectedRoute from './components/auth/ProtectedRoute'
import CloudConnectionsPage from './components/cloud/CloudConnectionsPage'
import SubscriptionPage from './components/subscription/SubscriptionPage'
import UserAnomaliesList from './components/anomalies/UserAnomaliesList'
import ReportAnomalyForm from './components/anomalies/ReportAnomalyForm'
import ModelFeedback from './components/anomalies/ModelFeedback'
import SimpleLogin from './SimpleLogin'

// Create theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// Main App component
function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <I18nextProvider i18n={i18n}>
        <AuthProvider>
          <Router>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/simple-login" element={<SimpleLogin />} />

              {/* Protected routes */}
              <Route path="/" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
              <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
              <Route path="/enterprises" element={<ProtectedRoute><Layout><EnterprisePage /></Layout></ProtectedRoute>} />
              <Route path="/cloud-connections" element={<ProtectedRoute><Layout><CloudConnectionsPage /></Layout></ProtectedRoute>} />
              <Route path="/subscription" element={<ProtectedRoute><Layout><SubscriptionPage /></Layout></ProtectedRoute>} />
              <Route path="/anomalies" element={<ProtectedRoute><Layout><UserAnomaliesList /></Layout></ProtectedRoute>} />
              <Route path="/report-anomaly" element={<ProtectedRoute><Layout><ReportAnomalyForm /></Layout></ProtectedRoute>} />
              <Route path="/model-feedback" element={<ProtectedRoute><Layout><ModelFeedback /></Layout></ProtectedRoute>} />

              {/* Redirect any unknown routes to dashboard */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Router>
        </AuthProvider>
      </I18nextProvider>
    </ThemeProvider>
  );
}

export default App
