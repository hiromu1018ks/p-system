import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getLeases, exportLeases } from '../api/leases'
import StatusBadge from '../components/StatusBadge'

const SUB_TYPE_LABELS = { land: '土地', building: '建物' }

export default function LeaseList() {
  const [leases, setLeases] = useState([])
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
      const data = await getLeases(params)
      setLeases(data.items)
      setTotal(data.total)
    } catch (err) { alert(err.message) }
    finally { setLoading(false) }
  }

  const handleSearch = (e) => { e.preventDefault(); setPage(1); load() }

  const handleExport = async () => {
    setExporting(true)
    try {
      await exportLeases(statusFilter)
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
        <h2>貸付案件一覧</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={handleExport} disabled={exporting}>{exporting ? 'エクスポート中...' : 'CSVエクスポート'}</button>
          <button onClick={() => navigate('/leases/new')}>新規登録</button>
        </div>
      </div>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input placeholder="借受者・目的で検索" value={q} onChange={e => setQ(e.target.value)} style={{ flex: 1 }} />
        <select value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1) }}>
          <option value="">全ステータス</option>
          <option value="draft">下書き</option>
          <option value="negotiating">協議中</option>
          <option value="pending_approval">決裁待ち</option>
          <option value="active">契約中</option>
          <option value="expired">期間終了</option>
          <option value="terminated">解約</option>
        </select>
        <button type="submit">検索</button>
      </form>

      {loading ? <p>読み込み中...</p> : (
        <>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd' }}>
                <th style={{ padding: 8, textAlign: 'left' }}>契約番号</th>
                <th style={{ padding: 8, textAlign: 'left' }}>種別</th>
                <th style={{ padding: 8, textAlign: 'left' }}>借受者</th>
                <th style={{ padding: 8, textAlign: 'left' }}>目的</th>
                <th style={{ padding: 8, textAlign: 'left' }}>期間</th>
                <th style={{ padding: 8, textAlign: 'right' }}>年間賃料</th>
                <th style={{ padding: 8, textAlign: 'center' }}>ステータス</th>
              </tr>
            </thead>
            <tbody>
              {leases.map((l) => (
                <tr key={l.id} style={{ borderBottom: '1px solid #eee', cursor: 'pointer' }}
                    onClick={() => navigate(`/leases/${l.id}`)}>
                  <td style={{ padding: 8 }}>{l.lease_number || '-'}</td>
                  <td style={{ padding: 8 }}>{SUB_TYPE_LABELS[l.property_sub_type] || l.property_sub_type}</td>
                  <td style={{ padding: 8 }}>{l.lessee_name}</td>
                  <td style={{ padding: 8 }}>{l.purpose}</td>
                  <td style={{ padding: 8, fontSize: 13 }}>{l.start_date} 〜 {l.end_date}</td>
                  <td style={{ padding: 8, textAlign: 'right' }}>{l.annual_rent ? l.annual_rent.toLocaleString() + '円' : '-'}</td>
                  <td style={{ padding: 8, textAlign: 'center' }}><StatusBadge status={l.status} caseType="lease" /></td>
                </tr>
              ))}
              {leases.length === 0 && (
                <tr><td colSpan={7} style={{ padding: 16, textAlign: 'center' }}>案件データがありません</td></tr>
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
