import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ToastContainer } from './components/ui'
import BottomNav from './components/BottomNav'
import LoginPage           from './pages/LoginPage'
import DashboardPage       from './pages/DashboardPage'
import TransactionsPage    from './pages/TransactionsPage'
import AddTransactionPage  from './pages/AddTransactionPage'
import VaultsPage          from './pages/VaultsPage'
import SettingsPage        from './pages/SettingsPage'
import SummaryPage         from './pages/SummaryPage'
import BulkListPage        from './pages/BulkListPage'
import BulkSpreadsheetPage from './pages/BulkSpreadsheetPage'

function ProtectedRoute({ children }) {
  const { isLoggedIn } = useAuth()
  return isLoggedIn ? children : <Navigate to="/login" replace />
}

function AppLayout({ children }) {
  return <>{children}<BottomNav /></>
}

function AppRoutes() {
  const { isLoggedIn } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={isLoggedIn ? <Navigate to="/dashboard" replace /> : <LoginPage />} />

      <Route path="/dashboard"        element={<ProtectedRoute><AppLayout><DashboardPage /></AppLayout></ProtectedRoute>} />
      <Route path="/transactions"     element={<ProtectedRoute><AppLayout><TransactionsPage /></AppLayout></ProtectedRoute>} />
      <Route path="/add"              element={<ProtectedRoute><AppLayout><AddTransactionPage /></AppLayout></ProtectedRoute>} />
      <Route path="/vaults"           element={<ProtectedRoute><AppLayout><VaultsPage /></AppLayout></ProtectedRoute>} />
      <Route path="/settings"         element={<ProtectedRoute><AppLayout><SettingsPage /></AppLayout></ProtectedRoute>} />
      <Route path="/summary"          element={<ProtectedRoute><AppLayout><SummaryPage /></AppLayout></ProtectedRoute>} />
      <Route path="/bulk"             element={<Navigate to="/add?tab=bulk" replace />} />
      <Route path="/bulk/list"        element={<Navigate to="/add?tab=bulk" replace />} />
      <Route path="/bulk/spreadsheet" element={<Navigate to="/add?tab=bulk" replace />} />

      <Route path="*" element={<Navigate to={isLoggedIn ? "/dashboard" : "/login"} replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastContainer />
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}