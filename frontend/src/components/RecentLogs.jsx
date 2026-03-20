// frontend/src/components/RecentLogs.jsx
const BADGE_STYLES = {
  CREATE: { bg: '#c6f6d5', color: '#276749' },
  UPDATE: { bg: '#dbeafe', color: '#1e40af' },
  DELETE: { bg: '#fed7d7', color: '#9b2c2c' },
  PDF_GEN: { bg: '#e9d8fd', color: '#6b46c1' },
  LOGIN: { bg: '#e2e8f0', color: '#4a5568' },
  EXPORT: { bg: '#e2e8f0', color: '#4a5568' },
}

function ActionBadge({ action }) {
  const style = BADGE_STYLES[action] || { bg: '#e2e8f0', color: '#4a5568' }
  return (
    <span style={{
      background: style.bg, color: style.color,
      padding: '2px 6px', borderRadius: 3, fontSize: 10, fontWeight: 600,
    }}>
      {action}
    </span>
  )
}

function formatDateTime(isoString) {
  if (!isoString) return '-'
  const d = new Date(isoString)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}/${dd} ${hh}:${mi}`
}

export default function RecentLogs({ logs }) {
  if (logs.length === 0) {
    return (
      <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#2d3748', marginBottom: 12 }}>最近の操作履歴</div>
        <p style={{ color: '#a0aec0', textAlign: 'center', padding: 12, margin: 0 }}>データなし</p>
      </div>
    )
  }

  return (
    <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#2d3748', marginBottom: 12 }}>最近の操作履歴</div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #e2e8f0' }}>
            <th style={{ padding: '6px 8px', textAlign: 'left', color: '#718096' }}>日時</th>
            <th style={{ padding: '6px 8px', textAlign: 'left', color: '#718096' }}>操作者</th>
            <th style={{ padding: '6px 8px', textAlign: 'left', color: '#718096' }}>操作</th>
            <th style={{ padding: '6px 8px', textAlign: 'left', color: '#718096' }}>対象</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
              <td style={{ padding: '6px 8px' }}>{formatDateTime(log.performed_at)}</td>
              <td style={{ padding: '6px 8px' }}>{log.user_name}</td>
              <td style={{ padding: '6px 8px' }}><ActionBadge action={log.action} /></td>
              <td style={{ padding: '6px 8px' }}>{log.summary || `${log.target_table} #${log.target_id}`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
