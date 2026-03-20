import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getLease, deleteLease, changeLeaseStatus, startLeaseRenewal } from '../api/leases'
import { getProperty } from '../api/properties'
import StatusBadge from '../components/StatusBadge'
import StatusTransitionButton from '../components/StatusTransitionButton'
import FeeCalculator from '../components/FeeCalculator'
import HistoryList from '../components/HistoryList'
import FileList from '../components/FileList'
import { generateLandLeasePdf, generateBuildingLeasePdf, generateRenewalPdf, downloadPdf, getDocumentHistory } from '../api/pdf'
import { useAuth } from '../contexts/AuthContext'

const SUB_TYPE_LABELS = { land: '土地', building: '建物' }
const PAYMENT_LABELS = { monthly: '月払', semiannual: '半期払', annual: '年払' }

export default function LeaseDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [lease, setLease] = useState(null)
  const [property, setProperty] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('basic')
  const [statusDialog, setStatusDialog] = useState(null)
  const [statusReason, setStatusReason] = useState('')
  const { user } = useAuth()

  useEffect(() => { load() }, [id])

  const load = async () => {
    setLoading(true)
    try {
      const leaseData = await getLease(id)
      setLease(leaseData)
      if (leaseData.property_id) {
        const prop = await getProperty(leaseData.property_id)
        setProperty(prop)
      }
    } catch (err) { alert('取得に失敗しました') }
    finally { setLoading(false) }
  }

  const handleStatusTransition = async (newStatus) => {
    if (newStatus === 'terminated') {
      setStatusDialog({ newStatus })
      return
    }
    await doStatusChange(newStatus, '')
  }

  const doStatusChange = async (newStatus, reason) => {
    try {
      await changeLeaseStatus(id, {
        new_status: newStatus,
        reason,
        expected_current_status: lease.status,
        expected_updated_at: lease.updated_at,
      })
      setStatusDialog(null)
      setStatusReason('')
      load()
    } catch (err) {
      if (err.message.includes('409')) {
        alert('他のユーザーが変更しました。画面を再読み込みしてください。')
        load()
      } else { alert(err.message) }
    }
  }

  const handleRenewal = async () => {
    if (!window.confirm('更新手続きを開始しますか？')) return
    try {
      const newLease = await startLeaseRenewal(id)
      navigate(`/leases/${newLease.id}`)
    } catch (err) { alert(err.message) }
  }

  const handleDelete = async () => {
    if (!window.confirm(`「${lease.lessee_name}」の案件を削除しますか？`)) return
    try { await deleteLease(id); navigate('/leases') }
    catch (err) { alert(err.message) }
  }

  if (loading) return <div>読み込み中...</div>
  if (!lease) return <div>案件が見つかりません</div>

  const userRole = user?.role || 'staff'

  const tabs = [
    { key: 'basic', label: '基本情報' },
    { key: 'fee', label: '賃料計算' },
    { key: 'files', label: '添付ファイル' },
    { key: 'history', label: '変更履歴' },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <button onClick={() => navigate('/leases')} style={{ marginRight: 12 }}>← 一覧に戻る</button>
          <h2 style={{ display: 'inline' }}>
            {lease.lease_number || '(下書き)'} - {lease.lessee_name}
          </h2>
          <StatusBadge status={lease.status} caseType="lease" />
        </div>
        <div>
          <button onClick={() => navigate(`/leases/${id}/edit`)} style={{ marginRight: 8 }}>編集</button>
          <button onClick={handleDelete} style={{ background: '#e53e3e' }}>削除</button>
        </div>
      </div>

      {lease.status !== 'expired' && lease.status !== 'terminated' && (
        <div style={{ marginBottom: 16, padding: 12, background: '#f7fafc', borderRadius: 4 }}>
          <div style={{ fontSize: 13, marginBottom: 8, color: '#718096' }}>ステータス操作</div>
          <StatusTransitionButton
            currentStatus={lease.status}
            userRole={userRole}
            onTransition={handleStatusTransition}
            caseType="lease"
          />
          {['active', 'expired'].includes(lease.status) && (
            <button onClick={handleRenewal} style={{ marginLeft: 16, padding: '4px 12px', fontSize: 13, border: '1px solid #38a169', borderRadius: 4, color: '#38a169', background: '#f0fff4', cursor: 'pointer' }}>
              更新手続きを開始
            </button>
          )}
        </div>
      )}

      {statusDialog && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'white', padding: 24, borderRadius: 8, minWidth: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
            <h3>解約</h3>
            <p style={{ marginBottom: 8 }}>理由を入力してください（必須）</p>
            <textarea value={statusReason} onChange={e => setStatusReason(e.target.value)} rows={3} style={{ width: '100%', marginBottom: 12 }} />
            <div>
              <button onClick={() => doStatusChange(statusDialog.newStatus, statusReason)} disabled={!statusReason} style={{ marginRight: 8 }}>実行</button>
              <button onClick={() => { setStatusDialog(null); setStatusReason('') }} style={{ background: '#a0aec0' }}>キャンセル</button>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', borderBottom: '2px solid #ddd', marginBottom: 16 }}>
        {tabs.map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            style={{ padding: '8px 16px', border: 'none', borderBottom: activeTab === tab.key ? '2px solid #2b6cb0' : '2px solid transparent', marginBottom: -2, fontWeight: activeTab === tab.key ? 'bold' : 'normal', color: activeTab === tab.key ? '#2b6cb0' : '#666', background: 'none', cursor: 'pointer' }}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'basic' && (
        <>
        <table style={{ width: '100%' }}>
          <tbody>
            {[
              ['契約番号', lease.lease_number || '（未採番）'],
              ['借受者氏名', lease.lessee_name],
              ['借受者住所', lease.lessee_address],
              ['連絡先', lease.lessee_contact || '-'],
              ['貸付目的', lease.purpose],
              ['対象財産', property ? `${property.property_code} ${property.name}` : '-'],
              ['財産種別', SUB_TYPE_LABELS[lease.property_sub_type] || lease.property_sub_type],
              ['契約期間', `${lease.start_date} 〜 ${lease.end_date}`],
              ['貸付面積・部屋番号', lease.leased_area || '-'],
              ['年間賃料', lease.annual_rent ? `${lease.annual_rent.toLocaleString()} 円` : '-'],
              ['支払方法', PAYMENT_LABELS[lease.payment_method] || '-'],
              ['更新連番', `${lease.renewal_seq} 回目`],
              ['登録日時', lease.created_at ? new Date(lease.created_at).toLocaleString('ja-JP') : '-'],
            ].map(([label, value]) => (
              <tr key={label} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '8px 16px', fontWeight: 500, width: 160, background: '#f7fafc' }}>{label}</td>
                <td style={{ padding: 8 }}>{value != null ? String(value) : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>

          {/* PDF出力ボタン */}
          <div style={{ marginTop: 16 }}>
            <h3 style={{ fontSize: 14, marginBottom: 8 }}>帳票出力</h3>
            {['active', 'expired'].includes(lease.status) && (
              <>
                <button
                  onClick={async () => {
                    try {
                      const result = await generateLandLeasePdf(lease.id)
                      await downloadPdf(result.id)
                    } catch (err) { alert(err.message) }
                  }}
                  style={{ marginRight: 8, padding: '6px 16px', fontSize: 13 }}
                >
                  土地貸付契約書を生成
                </button>
                {lease.property_sub_type === 'building' && (
                  <button
                    onClick={async () => {
                      try {
                        const result = await generateBuildingLeasePdf(lease.id)
                        await downloadPdf(result.id)
                      } catch (err) { alert(err.message) }
                    }}
                    style={{ marginRight: 8, padding: '6px 16px', fontSize: 13 }}
                  >
                    建物貸付契約書を生成
                  </button>
                )}
              </>
            )}
            {['active', 'expired'].includes(lease.status) && (
              <button
                onClick={async () => {
                  try {
                    const result = await generateRenewalPdf('lease', lease.id)
                    await downloadPdf(result.id)
                  } catch (err) { alert(err.message) }
                }}
                style={{ marginRight: 8, padding: '6px 16px', fontSize: 13 }}
              >
                更新通知文を生成
              </button>
            )}
            <button
              onClick={async () => {
                try {
                  const history = await getDocumentHistory('lease', lease.id)
                  if (history.length === 0) { alert('生成履歴がありません'); return }
                  await downloadPdf(history[0].id)
                } catch (err) { alert(err.message) }
              }}
              style={{ padding: '6px 16px', fontSize: 13, background: '#edf2f7', color: '#4a5568' }}
            >
              直近のPDFをダウンロード
            </button>
          </div>
        </>
      )}

      {activeTab === 'fee' && (
        <FeeCalculator caseId={parseInt(id)} caseType="lease" lease={lease} />
      )}

      {activeTab === 'files' && (
        <FileList relatedType="lease" relatedId={parseInt(id)} showUpload />
      )}

      {activeTab === 'history' && (
        <HistoryList caseType="lease" caseId={parseInt(id)} />
      )}
    </div>
  )
}
