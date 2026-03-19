import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getProperties, deleteProperty } from '../api/properties'

export default function PropertyList() {
  const [properties, setProperties] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [q, setQ] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadProperties()
  }, [page, typeFilter])

  const loadProperties = async () => {
    setLoading(true)
    try {
      const params = { page, per_page: 20 }
      if (q) params.q = q
      if (typeFilter) params.type = typeFilter
      const data = await getProperties(params)
      setProperties(data.items)
      setTotal(data.total)
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    loadProperties()
  }

  const handleDelete = async (id, name) => {
    if (!window.confirm(`「${name}」を削除しますか？`)) return
    try {
      await deleteProperty(id)
      loadProperties()
    } catch (err) {
      alert(err.message)
    }
  }

  const totalPages = Math.ceil(total / 20)

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2>財産台帳一覧</h2>
        <button onClick={() => navigate('/properties/new')}>新規登録</button>
      </div>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          type="text"
          placeholder="財産名・住所・地番で検索"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          style={{ flex: 1 }}
        />
        <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1) }}>
          <option value="">全区分</option>
          <option value="administrative">行政財産</option>
          <option value="general">普通財産</option>
        </select>
        <button type="submit">検索</button>
      </form>

      {loading ? (
        <p>読み込み中...</p>
      ) : (
        <>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd' }}>
                <th style={{ padding: 8, textAlign: 'left' }}>コード</th>
                <th style={{ padding: 8, textAlign: 'left' }}>財産名</th>
                <th style={{ padding: 8, textAlign: 'left' }}>区分</th>
                <th style={{ padding: 8, textAlign: 'left' }}>所在地</th>
                <th style={{ padding: 8, textAlign: 'left' }}>地目</th>
                <th style={{ padding: 8, textAlign: 'right' }}>面積(㎡)</th>
                <th style={{ padding: 8, textAlign: 'center' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {properties.map((p) => (
                <tr key={p.id} style={{ borderBottom: '1px solid #eee', cursor: 'pointer' }}
                    onClick={() => navigate(`/properties/${p.id}`)}>
                  <td style={{ padding: 8 }}>{p.property_code}</td>
                  <td style={{ padding: 8 }}>{p.name}</td>
                  <td style={{ padding: 8 }}>
                    <span style={{
                      padding: '2px 8px', borderRadius: 4, fontSize: 12,
                      background: p.property_type === 'administrative' ? '#bee3f8' : '#c6f6d5',
                    }}>
                      {p.property_type === 'administrative' ? '行政財産' : '普通財産'}
                    </span>
                  </td>
                  <td style={{ padding: 8 }}>{p.address || '-'}</td>
                  <td style={{ padding: 8 }}>{p.land_category || '-'}</td>
                  <td style={{ padding: 8, textAlign: 'right' }}>{p.area_sqm ?? '-'}</td>
                  <td style={{ padding: 8, textAlign: 'center' }}>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDelete(p.id, p.name) }}
                      style={{ padding: '4px 8px', fontSize: 12, background: '#e53e3e' }}
                    >
                      削除
                    </button>
                  </td>
                </tr>
              ))}
              {properties.length === 0 && (
                <tr><td colSpan={7} style={{ padding: 16, textAlign: 'center' }}>財産データがありません</td></tr>
              )}
            </tbody>
          </table>

          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
            <button disabled={page <= 1} onClick={() => setPage(page - 1)}>前へ</button>
            <span style={{ padding: '0 12px', lineHeight: '32px' }}>
              {page} / {totalPages || 1} ページ（全 {total} 件）
            </span>
            <button disabled={page >= totalPages} onClick={() => setPage(page + 1)}>次へ</button>
          </div>
        </>
      )}
    </div>
  )
}
