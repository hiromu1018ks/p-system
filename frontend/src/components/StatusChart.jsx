// frontend/src/components/StatusChart.jsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const STATUS_LABELS = {
  draft: '下書き',
  submitted: '申請受付済み',
  under_review: '審査中',
  pending_approval: '決裁待ち',
  approved: '決裁完了',
  issued: '交付済み',
  negotiating: '協議中',
  active: '契約中',
  rejected: '差戻し',
  expired: '期間終了',
  cancelled: '取消',
  terminated: '解約',
}

export default function StatusChart({ statusDistribution }) {
  const { permissions, leases } = statusDistribution

  const allStatuses = new Set([
    ...permissions.map(p => p.status),
    ...leases.map(l => l.status),
  ])

  const data = [...allStatuses].map(status => ({
    name: STATUS_LABELS[status] || status,
    使用許可: permissions.find(p => p.status === status)?.count || 0,
    普通財産貸付: leases.find(l => l.status === status)?.count || 0,
  }))

  if (data.length === 0) {
    return <p style={{ color: '#a0aec0', textAlign: 'center', padding: 20 }}>データなし</p>
  }

  return (
    <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: '#2d3748', marginBottom: 12 }}>ステータス別件数</div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="使用許可" fill="#90cdf4" radius={[2, 2, 0, 0]} />
          <Bar dataKey="普通財産貸付" fill="#3182ce" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
