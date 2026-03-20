// frontend/src/components/ExpiryAlerts.jsx
import { useNavigate } from 'react-router-dom'

function getUrgencyStyle(days) {
  if (days <= 7) return { bg: '#fff5f5', border: '#e53e3e', text: '#e53e3e' }
  if (days <= 15) return { bg: '#fffaf0', border: '#ed8936', text: '#ed8936' }
  return { bg: '#fffff0', border: '#d69e2e', text: '#d69e2e' }
}

export default function ExpiryAlerts({ alerts }) {
  const navigate = useNavigate()

  if (alerts.length === 0) {
    return (
      <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#2d3748', marginBottom: 12 }}>有効期限アラート</div>
        <p style={{ color: '#38a169', textAlign: 'center', padding: 12, margin: 0 }}>期限切れ間近の案件はありません</p>
      </div>
    )
  }

  return (
    <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#e53e3e', marginBottom: 12 }}>有効期限アラート</div>
      <div>
        {alerts.map(alert => {
          const style = getUrgencyStyle(alert.days_remaining)
          const route = alert.case_type === 'permission' ? `/permissions/${alert.case_id}` : `/leases/${alert.case_id}`
          return (
            <div
              key={`${alert.case_type}-${alert.case_id}`}
              onClick={() => navigate(route)}
              style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: 8, background: style.bg, borderRadius: 4,
                marginBottom: 6, borderLeft: `3px solid ${style.border}`, cursor: 'pointer',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{alert.case_number} / {alert.applicant_name}</div>
                <div style={{ fontSize: 11, color: '#718096' }}>{alert.property_name}</div>
              </div>
              <div style={{ color: style.text, fontWeight: 700, fontSize: 13, whiteSpace: 'nowrap' }}>
                あと{alert.days_remaining}日
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
