const PERMISSION_STATUS_LABELS = {
  draft: '下書き',
  submitted: '申請受付済み',
  under_review: '審査中',
  pending_approval: '決裁待ち',
  approved: '決裁完了',
  issued: '交付済み',
  rejected: '差戻し',
  expired: '期間終了',
  cancelled: '取消',
}

const PERMISSION_STATUS_COLORS = {
  draft: '#e2e8f0',
  submitted: '#bee3f8',
  under_review: '#fefcbf',
  pending_approval: '#fefcbf',
  approved: '#c6f6d5',
  issued: '#9ae6b4',
  rejected: '#fed7d7',
  expired: '#e2e8f0',
  cancelled: '#fed7d7',
}

const LEASE_STATUS_LABELS = {
  draft: '下書き',
  negotiating: '協議中',
  pending_approval: '決裁待ち',
  active: '契約中',
  expired: '期間終了',
  terminated: '解約',
}

const LEASE_STATUS_COLORS = {
  draft: '#e2e8f0',
  negotiating: '#fefcbf',
  pending_approval: '#fefcbf',
  active: '#c6f6d5',
  expired: '#e2e8f0',
  terminated: '#fed7d7',
}

export default function StatusBadge({ status, caseType }) {
  const labels = caseType === 'lease' ? LEASE_STATUS_LABELS : PERMISSION_STATUS_LABELS
  const colors = caseType === 'lease' ? LEASE_STATUS_COLORS : PERMISSION_STATUS_COLORS
  const label = labels[status] || status
  const bg = colors[status] || '#e2e8f0'

  return (
    <span style={{
      padding: '2px 10px',
      borderRadius: 4,
      fontSize: 12,
      fontWeight: 500,
      background: bg,
      color: '#1a202c',
    }}>
      {label}
    </span>
  )
}
