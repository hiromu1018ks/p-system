import { useState, useEffect } from 'react'
import { getDashboardSummary } from '../api/dashboard'
import StatusChart from '../components/StatusChart'
import ExpiryAlerts from '../components/ExpiryAlerts'
import RecentLogs from '../components/RecentLogs'

function KpiCard({ label, value, color, subtext }) {
  return (
    <div style={{
      background: 'white', border: color ? `1px solid ${color}33` : '1px solid #e2e8f0',
      borderLeft: color ? `3px solid ${color}` : 'none',
      borderRadius: 6, padding: 16, textAlign: 'center',
      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
    }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: color || '#2b6cb0' }}>{value}</div>
      <div style={{ fontSize: 12, color: '#718096', marginTop: 4 }}>{label}</div>
      {subtext && <div style={{ fontSize: 10, color: '#a0aec0', marginTop: 2 }}>{subtext}</div>}
    </div>
  )
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboardSummary()
      .then(setData)
      .catch(err => alert(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
        {/* KPI Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
          <KpiCard
            label="使用許可案件中"
            value={loading ? '...' : (data?.active_permissions ?? 0)}
            color="#2b6cb0"
            subtext="(有効案件のみ)"
          />
          <KpiCard
            label="貸付案件中"
            value={loading ? '...' : (data?.active_leases ?? 0)}
            color="#2b6cb0"
            subtext="(有効案件のみ)"
          />
          <KpiCard
            label="期限切れ間近"
            value={loading ? '...' : (data?.expiring_soon ?? 0)}
            color="#e53e3e"
            subtext="(30日以内)"
          />
          <KpiCard
            label="今月新規"
            value={loading ? '...' : (data?.new_this_month ?? 0)}
            color="#38a169"
            subtext="(許可+貸付)"
          />
        </div>

        {/* FY Total */}
        <div style={{ display: 'grid', gridTemplateColumns: '200px', gap: 12, marginBottom: 20 }}>
          <div style={{
            background: 'white', border: '1px solid #e2e8f0', borderRadius: 6,
            padding: 16, textAlign: 'center', boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
          }}>
            <div style={{ fontSize: 12, color: '#718096', marginBottom: 4 }}>
              {loading ? '...' : data?.fy_label}累計
            </div>
            <div style={{ fontSize: 32, fontWeight: 700, color: '#2d3748' }}>
              {loading ? '...' : (data?.fy_total ?? 0)}
            </div>
          </div>
        </div>

        {/* Chart + Alerts */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
          {loading ? (
            <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, textAlign: 'center' }}>
              <p>読み込み中...</p>
            </div>
          ) : data ? (
            <>
              <StatusChart statusDistribution={data.status_distribution} />
              <ExpiryAlerts alerts={data.expiry_alerts} />
            </>
          ) : null}
        </div>

        {/* Recent Logs */}
        {loading ? (
          <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 6, padding: 16, textAlign: 'center' }}>
            <p>読み込み中...</p>
          </div>
        ) : data ? (
          <RecentLogs logs={data.recent_logs} />
        ) : null}
    </div>
  )
}
