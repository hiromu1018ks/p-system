import { useState, useEffect } from 'react'
import { getPropertyHistory } from '../api/properties'

const OPERATION_LABELS = {
  CREATE: '新規登録',
  UPDATE: '更新',
  DELETE: '削除',
  RESTORE: '復元',
  STATUS_CHANGE: 'ステータス変更',
}

export default function HistoryList({ propertyId }) {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!propertyId) return
    getPropertyHistory(propertyId)
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false))
  }, [propertyId])

  if (loading) return <p>読み込み中...</p>
  if (!history.length) return <p>変更履歴はありません</p>

  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr style={{ borderBottom: '2px solid #ddd' }}>
          <th style={{ padding: 8, textAlign: 'left' }}>日時</th>
          <th style={{ padding: 8, textAlign: 'left' }}>操作</th>
          <th style={{ padding: 8, textAlign: 'left' }}>理由</th>
          <th style={{ padding: 8, textAlign: 'left' }}>操作者ID</th>
        </tr>
      </thead>
      <tbody>
        {history.map((h) => (
          <tr key={h.id} style={{ borderBottom: '1px solid #eee' }}>
            <td style={{ padding: 8 }}>
              {h.changed_at ? new Date(h.changed_at).toLocaleString('ja-JP') : '-'}
            </td>
            <td style={{ padding: 8 }}>
              <span
                style={{
                  padding: '2px 8px', borderRadius: 4, fontSize: 12,
                  background: h.operation_type === 'DELETE' ? '#fed7d7' : '#c6f6d5',
                  color: h.operation_type === 'DELETE' ? '#c53030' : '#276749',
                }}
              >
                {OPERATION_LABELS[h.operation_type] || h.operation_type}
              </span>
            </td>
            <td style={{ padding: 8 }}>{h.reason || '-'}</td>
            <td style={{ padding: 8 }}>{h.changed_by}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
