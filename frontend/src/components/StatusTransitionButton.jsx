// §2.4.2 に基づく遷移ルール
const PERMISSION_TRANSITIONS = {
  draft: [{ to: 'submitted', label: '受付登録' }],
  submitted: [{ to: 'under_review', label: '審査開始' }],
  under_review: [
    { to: 'rejected', label: '差戻し', adminOnly: true },
    { to: 'pending_approval', label: '決裁上申' },
  ],
  pending_approval: [
    { to: 'rejected', label: '差戻し', adminOnly: true },
    { to: 'approved', label: '決裁完了', adminOnly: true },
  ],
  approved: [
    { to: 'issued', label: '交付済み' },
    { to: 'expired', label: '期間満了', adminOnly: true },
    { to: 'cancelled', label: '取消', adminOnly: true },
  ],
  issued: [
    { to: 'expired', label: '期間満了', adminOnly: true },
    { to: 'cancelled', label: '取消', adminOnly: true },
  ],
  rejected: [{ to: 'submitted', label: '再申請' }],
}

export default function StatusTransitionButton({ currentStatus, userRole, onTransition }) {
  const transitions = PERMISSION_TRANSITIONS[currentStatus] || []

  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      {transitions.map(({ to, label, adminOnly }) => {
        if (adminOnly && userRole !== 'admin') {
          return (
            <span
              key={to}
              title="管理者権限が必要です"
              style={{
                padding: '4px 12px',
                fontSize: 13,
                color: '#a0aec0',
                border: '1px solid #e2e8f0',
                borderRadius: 4,
                cursor: 'not-allowed',
                background: '#f7fafc',
              }}
            >
              {label}
            </span>
          )
        }
        return (
          <button
            key={to}
            onClick={() => onTransition(to)}
            style={{
              padding: '4px 12px',
              fontSize: 13,
              border: '1px solid #ccc',
              borderRadius: 4,
              cursor: 'pointer',
              background: to === 'rejected' || to === 'cancelled' ? '#fff5f5' : '#ebf8ff',
              color: to === 'rejected' || to === 'cancelled' ? '#c53030' : '#2b6cb0',
            }}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
