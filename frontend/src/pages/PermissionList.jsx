import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPermissions, exportPermissions } from '../api/permissions'
import StatusBadge from '../components/StatusBadge'

export default function PermissionList() {
  const [permissions, setPermissions] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  const navigate = useNavigate()

  useEffect(() => { load() }, [page, statusFilter])

  const load = async () => {
    setLoading(true)
    try {
      const params = { page, per_page: 20 }
      if (statusFilter) params.status = statusFilter
      if (q) params.q = q
      const data = await getPermissions(params)
      setPermissions(data.items)
      setTotal(data.total)
    } catch (err) { alert(err.message) }
    finally { setLoading(false) }
  }

  const handleSearch = (e) => { e.preventDefault(); setPage(1); load() }

  const handleExport = async () => {
    setExporting(true)
    try {
      await exportPermissions(statusFilter)
    } catch (err) {
      alert(err.message)
    } finally {
      setExporting(false)
    }
  }

  const totalPages = Math.ceil(total / 20)

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>使用許可案件一覧</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={handleExport} disabled={exporting}>{exporting ? 'エクスポート中...' : 'CSVエクスポート'}</button>
          <button onClick={() => navigate('/permissions/new')}>新規登録</button>
        </div>
      </div>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input placeholder="申請者・目的で検索" value={q} onChange={e => setQ(e.target.value)} style={{ flex: 1 }} />
        <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }}>
          <option value="">全ステータス</option>
          <option value="draft">下書き</option>
          <option value="submitted">申請受付済み</option>
          <option value="under_review">審査中</option>
          <option value="pending_approval">決裁待ち</option>
          <option value="approved">決裁完了</option>
          <option value="issued">交付済み</option>
          <option value="rejected">差戻し</option>
          <option value="expired">期間終了</option>
          <option value="cancelled">取消</option>
        </select>
        <button type="submit">検索</button>
      </form>

      {loading ? <p>読み込み中...</p> : (
        <>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd' }}>
                <th style={{ padding: 8, textAlign: 'left' }}>許可番号</th>
                <th style={{ padding: 8, textAlign: 'left' }}>申請者</th>
                <th style={{ padding: 8, textAlign: 'left' }}>目的</th>
                <th style={{ padding: 8, textAlign: 'left' }}>期間</th>
                <th style={{ padding: 8, textAlign: 'right' }}>使用料</th>
                <th style={{ padding: 8, textAlign: 'center' }}>ステータス</th>
              </tr>
            </thead>
            <tbody>
              {permissions.map((p) => (
                <tr key={p.id} style={{ borderBottom: '1px solid #eee', cursor: 'pointer' }}
                    onClick={() => navigate(`/permissions/${p.id}`)}>
                  <td style={{ padding: 8 }}>{p.permission_number || '-'}</td>
                  <td style={{ padding: 8 }}>{p.applicant_name}</td>
                  <td style={{ padding: 8 }}>{p.purpose}</td>
                  <td style={{ padding: 8, fontSize: 13 }}>{p.start_date} 〜 {p.end_date}</td>
                  <td style={{ padding: 8, textAlign: 'right' }}>{p.fee_amount ? p.fee_amount.toLocaleString() + '円' : '-'}</td>
                  <td style={{ padding: 8, textAlign: 'center' }}><StatusBadge status={p.status} /></td>
                </tr>
              ))}
              {permissions.length === 0 && (
                <tr><td colSpan={6} style={{ padding: 16, textAlign: 'center' }}>案件データがありません</td></tr>
              )}
            </tbody>
          </table>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
            <button disabled={page <= 1} onClick={() => setPage(page - 1)}>前へ</button>
            <span style={{ padding: '0 12px', lineHeight: '32px' }}>{page} / {totalPages || 1} ページ（全 {total} 件）</span>
            <button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>次へ</button>
          </div>
        </>
      )}
    </div>
  )
}
