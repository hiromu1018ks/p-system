import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { logout } from '../api/auth'

const NAV_ITEMS = [
  { path: '/dashboard', label: 'ダッシュボード' },
  { path: '/properties', label: '財産台帳' },
  { path: '/permissions', label: '使用許可' },
  { path: '/leases', label: '普通財産貸付' },
]

export default function Layout() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = async () => {
    await logout()
    setUser(null)
    navigate('/login')
  }

  const isActive = (path) => location.pathname.startsWith(path)

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside className="sidebar">
        <div className="sidebar-title">自治体財産管理システム</div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map(item => (
            <button
              key={item.path}
              className={`sidebar-link ${isActive(item.path) ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
            >
              {item.label}
            </button>
          ))}
          {user?.role === 'admin' && (
            <>
              <div style={{ borderTop: '1px solid rgba(255,255,255,0.15)', margin: '8px 0' }} />
              <button
                className={`sidebar-link ${isActive('/master-admin') ? 'active' : ''}`}
                onClick={() => navigate('/master-admin')}
              >
                マスタ管理
              </button>
              <button
                className={`sidebar-link ${isActive('/bulk-fee-update') ? 'active' : ''}`}
                onClick={() => navigate('/bulk-fee-update')}
              >
                一括賃料改定
              </button>
            </>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="sidebar-user">
            {user?.display_name}（{user?.department}）
          </div>
          <button className="sidebar-logout" onClick={handleLogout}>
            ログアウト
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
