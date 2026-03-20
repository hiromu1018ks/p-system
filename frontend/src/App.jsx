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
import Layout from './components/Layout'
import './App.css'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/properties" element={<PropertyList />} />
            <Route path="/properties/:id" element={<PropertyDetail />} />
            <Route path="/properties/new" element={<PropertyForm />} />
            <Route path="/properties/:id/edit" element={<PropertyForm />} />
            <Route path="/permissions" element={<PermissionList />} />
            <Route path="/permissions/:id" element={<PermissionDetail />} />
            <Route path="/permissions/new" element={<PermissionForm />} />
            <Route path="/permissions/:id/edit" element={<PermissionForm />} />
            <Route path="/leases" element={<LeaseList />} />
            <Route path="/leases/:id" element={<LeaseDetail />} />
            <Route path="/leases/new" element={<LeaseForm />} />
            <Route path="/leases/:id/edit" element={<LeaseForm />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
