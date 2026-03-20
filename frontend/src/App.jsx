import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import PropertyList from './pages/PropertyList'
import PropertyDetail from './pages/PropertyDetail'
import PropertyForm from './pages/PropertyForm'
import PermissionList from './pages/PermissionList'
import PermissionDetail from './pages/PermissionDetail'
import PermissionForm from './pages/PermissionForm'
import LeaseList from './pages/LeaseList'
import LeaseDetail from './pages/LeaseDetail'
import LeaseForm from './pages/LeaseForm'
import ProtectedRoute from './components/ProtectedRoute'
import './App.css'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/properties"
            element={
              <ProtectedRoute>
                <PropertyList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/properties/:id"
            element={
              <ProtectedRoute>
                <PropertyDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/properties/new"
            element={
              <ProtectedRoute>
                <PropertyForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/properties/:id/edit"
            element={
              <ProtectedRoute>
                <PropertyForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/permissions"
            element={<ProtectedRoute><PermissionList /></ProtectedRoute>}
          />
          <Route
            path="/permissions/:id"
            element={<ProtectedRoute><PermissionDetail /></ProtectedRoute>}
          />
          <Route
            path="/permissions/new"
            element={<ProtectedRoute><PermissionForm /></ProtectedRoute>}
          />
          <Route
            path="/permissions/:id/edit"
            element={<ProtectedRoute><PermissionForm /></ProtectedRoute>}
          />
          <Route
            path="/leases"
            element={<ProtectedRoute><LeaseList /></ProtectedRoute>}
          />
          <Route
            path="/leases/:id"
            element={<ProtectedRoute><LeaseDetail /></ProtectedRoute>}
          />
          <Route
            path="/leases/new"
            element={<ProtectedRoute><LeaseForm /></ProtectedRoute>}
          />
          <Route
            path="/leases/:id/edit"
            element={<ProtectedRoute><LeaseForm /></ProtectedRoute>}
          />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
