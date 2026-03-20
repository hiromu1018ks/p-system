import { useAuth } from '../contexts/AuthContext'
import { logout } from '../api/auth'
import { useNavigate } from 'react-router-dom'

export default function DashboardPlaceholder() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    setUser(null)
    navigate('/login')
  }

  return (
    <div>
      <header>
        <h1>自治体財産管理システム</h1>
        <div>
          <span>{user?.display_name} ({user?.role})</span>
          <button onClick={handleLogout}>ログアウト</button>
        </div>
      </header>
      <main>
        <h2>ダッシュボード（開発中）</h2>
        <p>認証・共通基盤の動作確認用ページです。</p>
        <p>Plan 2 以降でダッシュボードを実装します。</p>
        <p><a href="/properties" style={{ color: '#2b6cb0' }}>財産台帳を開く</a></p>
        <p><a href="/permissions" style={{ color: '#2b6cb0' }}>使用許可案件を開く</a></p>
      </main>
    </div>
  )
}
