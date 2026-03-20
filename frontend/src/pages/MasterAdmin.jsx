import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { getUnitPrices, createUnitPrice } from '../api/fees'
import { getUsers, createUser, unlockUser } from '../api/auth'

const TABS = [
  { key: 'unit_prices', label: '単価マスタ' },
  { key: 'users', label: 'ユーザー管理' },
]

const PROPERTY_TYPES = [
  { value: '', label: '選択してください' },
  { value: 'land', label: '土地' },
  { value: 'building', label: '建物' },
  { value: 'facility', label: '施設' },
  { value: 'equipment', label: '設備' },
  { value: 'other', label: 'その他' },
]

const ROLES = [
  { value: 'admin', label: '管理者' },
  { value: 'staff', label: 'スタッフ' },
  { value: 'viewer', label: '閲覧者' },
]

const buttonStyle = {
  padding: '8px 16px',
  background: '#2b6cb0',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '14px',
}

const buttonDisabledStyle = {
  ...buttonStyle,
  opacity: 0.6,
  cursor: 'not-allowed',
}

const inputStyle = {
  padding: '8px 12px',
  border: '1px solid #ccc',
  borderRadius: '4px',
  fontSize: '14px',
}

export default function MasterAdmin() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('unit_prices')

  if (user?.role !== 'admin') {
    return <p>管理者のみアクセス可能です。</p>
  }

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>マスタ管理</h2>
      <div style={{ display: 'flex', gap: 0, marginBottom: 24, borderBottom: '2px solid #ddd' }}>
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '10px 20px',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: activeTab === tab.key ? 'bold' : 'normal',
              color: activeTab === tab.key ? '#2b6cb0' : '#666',
              borderBottom: activeTab === tab.key ? '2px solid #2b6cb0' : '2px solid transparent',
              marginBottom: '-2px',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {activeTab === 'unit_prices' && <UnitPriceTab />}
      {activeTab === 'users' && <UserTab />}
    </div>
  )
}

function UnitPriceTab() {
  const [unitPrices, setUnitPrices] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ property_type: '', usage: '', unit_price: '', start_date: '' })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try {
      const data = await getUnitPrices()
      setUnitPrices(data)
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.property_type || !form.usage || !form.unit_price || !form.start_date) {
      alert('すべての項目を入力してください。')
      return
    }
    setSubmitting(true)
    try {
      await createUnitPrice({
        property_type: form.property_type,
        usage: form.usage,
        unit_price: parseInt(form.unit_price, 10),
        start_date: form.start_date,
      })
      setForm({ property_type: '', usage: '', unit_price: '', start_date: '' })
      setShowForm(false)
      await load()
    } catch (err) {
      alert(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3>単価一覧</h3>
        <button style={buttonStyle} onClick={() => setShowForm(!showForm)}>
          {showForm ? '閉じる' : '新規登録'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} style={{
          background: '#f8f9fa',
          padding: 16,
          borderRadius: 8,
          marginBottom: 16,
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
          gap: 12,
          alignItems: 'end',
        }}>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>財産種別</label>
            <select value={form.property_type} onChange={e => setForm({ ...form, property_type: e.target.value })} style={{ ...inputStyle, width: '100%' }}>
              {PROPERTY_TYPES.map(pt => (
                <option key={pt.value} value={pt.value}>{pt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>用途</label>
            <input value={form.usage} onChange={e => setForm({ ...form, usage: e.target.value })} placeholder="用途を入力" style={{ ...inputStyle, width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>単価（円）</label>
            <input type="number" value={form.unit_price} onChange={e => setForm({ ...form, unit_price: e.target.value })} placeholder="0" min="0" style={{ ...inputStyle, width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>適用開始日</label>
            <input type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} style={{ ...inputStyle, width: '100%' }} />
          </div>
          <div>
            <button type="submit" disabled={submitting} style={submitting ? buttonDisabledStyle : buttonStyle}>
              {submitting ? '登録中...' : '登録'}
            </button>
          </div>
        </form>
      )}

      {loading ? <p>読み込み中...</p> : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: 8, textAlign: 'left' }}>財産種別</th>
              <th style={{ padding: 8, textAlign: 'left' }}>用途</th>
              <th style={{ padding: 8, textAlign: 'right' }}>単価（円）</th>
              <th style={{ padding: 8, textAlign: 'left' }}>適用開始日</th>
              <th style={{ padding: 8, textAlign: 'left' }}>適用終了日</th>
            </tr>
          </thead>
          <tbody>
            {unitPrices.map(up => (
              <tr key={up.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: 8 }}>{up.property_type}</td>
                <td style={{ padding: 8 }}>{up.usage}</td>
                <td style={{ padding: 8, textAlign: 'right' }}>{up.unit_price?.toLocaleString() || '-'}</td>
                <td style={{ padding: 8 }}>{up.start_date || '-'}</td>
                <td style={{ padding: 8 }}>{up.end_date || '-'}</td>
              </tr>
            ))}
            {unitPrices.length === 0 && (
              <tr><td colSpan={5} style={{ padding: 16, textAlign: 'center' }}>単価データがありません</td></tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}

function UserTab() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ username: '', password: '', display_name: '', role: 'staff', department: '' })
  const [submitting, setSubmitting] = useState(false)
  const [unlockingId, setUnlockingId] = useState(null)

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try {
      const data = await getUsers()
      setUsers(data)
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.username || !form.password || !form.display_name || !form.department) {
      alert('すべての項目を入力してください。')
      return
    }
    setSubmitting(true)
    try {
      await createUser(form)
      setForm({ username: '', password: '', display_name: '', role: 'staff', department: '' })
      setShowForm(false)
      await load()
    } catch (err) {
      alert(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleUnlock = async (userId) => {
    if (!window.confirm('ロックを解除しますか？')) return
    setUnlockingId(userId)
    try {
      await unlockUser(userId)
      await load()
    } catch (err) {
      alert(err.message)
    } finally {
      setUnlockingId(null)
    }
  }

  const roleLabel = (role) => {
    const found = ROLES.find(r => r.value === role)
    return found ? found.label : role
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3>ユーザー一覧</h3>
        <button style={buttonStyle} onClick={() => setShowForm(!showForm)}>
          {showForm ? '閉じる' : '新規ユーザー登録'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} style={{
          background: '#f8f9fa',
          padding: 16,
          borderRadius: 8,
          marginBottom: 16,
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
          gap: 12,
          alignItems: 'end',
        }}>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>ユーザー名</label>
            <input value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} placeholder="username" style={{ ...inputStyle, width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>パスワード</label>
            <input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder="パスワード" style={{ ...inputStyle, width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>表示名</label>
            <input value={form.display_name} onChange={e => setForm({ ...form, display_name: e.target.value })} placeholder="田中太郎" style={{ ...inputStyle, width: '100%' }} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>権限</label>
            <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })} style={{ ...inputStyle, width: '100%' }}>
              {ROLES.map(r => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>部署</label>
            <input value={form.department} onChange={e => setForm({ ...form, department: e.target.value })} placeholder="財政課" style={{ ...inputStyle, width: '100%' }} />
          </div>
          <div>
            <button type="submit" disabled={submitting} style={submitting ? buttonDisabledStyle : buttonStyle}>
              {submitting ? '登録中...' : '登録'}
            </button>
          </div>
        </form>
      )}

      {loading ? <p>読み込み中...</p> : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: 8, textAlign: 'left' }}>ユーザー名</th>
              <th style={{ padding: 8, textAlign: 'left' }}>表示名</th>
              <th style={{ padding: 8, textAlign: 'left' }}>権限</th>
              <th style={{ padding: 8, textAlign: 'left' }}>部署</th>
              <th style={{ padding: 8, textAlign: 'center' }}>状態</th>
              <th style={{ padding: 8, textAlign: 'left' }}>作成日</th>
              <th style={{ padding: 8, textAlign: 'center' }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: 8 }}>{u.username}</td>
                <td style={{ padding: 8 }}>{u.display_name}</td>
                <td style={{ padding: 8 }}>{roleLabel(u.role)}</td>
                <td style={{ padding: 8 }}>{u.department}</td>
                <td style={{ padding: 8, textAlign: 'center' }}>
                  {u.is_locked ? (
                    <span style={{ color: '#e53e3e', fontWeight: 'bold' }}>ロック中</span>
                  ) : (
                    <span style={{ color: '#38a169' }}>有効</span>
                  )}
                </td>
                <td style={{ padding: 8, fontSize: 13 }}>{u.created_at ? u.created_at.slice(0, 10) : '-'}</td>
                <td style={{ padding: 8, textAlign: 'center' }}>
                  {u.is_locked && (
                    <button
                      onClick={() => handleUnlock(u.id)}
                      disabled={unlockingId === u.id}
                      style={unlockingId === u.id ? buttonDisabledStyle : { ...buttonStyle, background: '#dd6b20', padding: '4px 12px', fontSize: '13px' }}
                    >
                      {unlockingId === u.id ? '解除中...' : 'ロック解除'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr><td colSpan={7} style={{ padding: 16, textAlign: 'center' }}>ユーザーデータがありません</td></tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  )
}
