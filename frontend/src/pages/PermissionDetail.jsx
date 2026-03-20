import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getPermission, deletePermission, changePermissionStatus, startRenewal, getPermissionHistory } from '../api/permissions'
import { getProperty } from '../api/properties'
import StatusBadge from '../components/StatusBadge'
import StatusTransitionButton from '../components/StatusTransitionButton'
import FeeCalculator from '../components/FeeCalculator'
import HistoryList from '../components/HistoryList'
import FileList from '../components/FileList'

export default function PermissionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [permission, setPermission] = useState(null)
  const [property, setProperty] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('basic')
  const [statusDialog, setStatusDialog] = useState(null) // { newStatus }
  const [statusReason, setStatusReason] = useState('')

  useEffect(() => {
    load()
  }, [id])

  const load = async () => {
    setLoading(true)
    try {
      const [perm, hist] = await Promise.all([getPermission(id), getPermissionHistory(id)])
      setPermission(perm)
      setHistory(hist)
      if (perm.property_id) {
        const prop = await getProperty(perm.property_id)
        setProperty(prop)
      }
    } catch (err) { alert('取得に失敗しました') }
    finally { setLoading(false) }
  }

  const handleStatusTransition = async (newStatus) => {
    const requiresReason = ['rejected', 'cancelled'].includes(newStatus)
    if (requiresReason) {
      setStatusDialog({ newStatus })
      return
    }
    await doStatusChange(newStatus, '')
  }

  const doStatusChange = async (newStatus, reason) => {
    try {
      await changePermissionStatus(id, {
        new_status: newStatus,
        reason,
        expected_current_status: permission.status,
        expected_updated_at: permission.updated_at,
      })
      setStatusDialog(null)
      setStatusReason('')
      load()
    } catch (err) {
      if (err.message.includes('409')) {
        alert('他のユーザーが変更しました。画面を再読み込みしてください。')
        load()
      } else {
        alert(err.message)
      }
    }
  }

  const handleRenewal = async () => {
    if (!window.confirm('更新手続きを開始しますか？')) return
    try {
      const newPerm = await startRenewal(id)
      navigate(`/permissions/${newPerm.id}`)
    } catch (err) { alert(err.message) }
  }

  const handleDelete = async () => {
    if (!window.confirm(`「${permission.applicant_name}」の案件を削除しますか？`)) return
    try { await deletePermission(id); navigate('/permissions') }
    catch (err) { alert(err.message) }
  }

  if (loading) return <div>読み込み中...</div>
  if (!permission) return <div>案件が見つかりません</div>

  const userRole = JSON.parse(sessionStorage.getItem('user') || '{}').role || 'staff'

  const tabs = [
    { key: 'basic', label: '基本情報' },
    { key: 'fee', label: '料金計算' },
    { key: 'files', label: '添付ファイル' },
    { key: 'history', label: '変更履歴' },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <button onClick={() => navigate('/permissions')} style={{ marginRight: 12 }}>← 一覧に戻る</button>
          <h2 style={{ display: 'inline' }}>
            {permission.permission_number || '(下書き)'} - {permission.applicant_name}
          </h2>
          <StatusBadge status={permission.status} />
        </div>
        <div>
          <button onClick={() => navigate(`/permissions/${id}/edit`)} style={{ marginRight: 8 }}>編集</button>
          <button onClick={handleDelete} style={{ background: '#e53e3e' }}>削除</button>
        </div>
      </div>

      {/* ステータス変更ボタン */}
      {permission.status !== 'expired' && permission.status !== 'cancelled' && (
        <div style={{ marginBottom: 16, padding: 12, background: '#f7fafc', borderRadius: 4 }}>
          <div style={{ fontSize: 13, marginBottom: 8, color: '#718096' }}>ステータス操作</div>
          <StatusTransitionButton
            currentStatus={permission.status}
            userRole={userRole}
            onTransition={handleStatusTransition}
          />
          {['approved', 'issued', 'expired'].includes(permission.status) && (
            <button onClick={handleRenewal} style={{ marginLeft: 16, padding: '4px 12px', fontSize: 13, border: '1px solid #38a169', borderRadius: 4, color: '#38a169', background: '#f0fff4', cursor: 'pointer' }}>
              更新手続きを開始
            </button>
          )}
        </div>
      )}

      {/* ステータス変更ダイアログ */}
      {statusDialog && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'white', padding: 24, borderRadius: 8, minWidth: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
            <h3>{statusDialog.newStatus === 'rejected' ? '差戻し' : '取消'}</h3>
            <p style={{ marginBottom: 8 }}>理由を入力してください（必須）</p>
            <textarea value={statusReason} onChange={e => setStatusReason(e.target.value)} rows={3} style={{ width: '100%', marginBottom: 12 }} />
            <div>
              <button onClick={() => doStatusChange(statusDialog.newStatus, statusReason)} disabled={!statusReason} style={{ marginRight: 8 }}>実行</button>
              <button onClick={() => { setStatusDialog(null); setStatusReason('') }} style={{ background: '#a0aec0' }}>キャンセル</button>
            </div>
          </div>
        </div>
      )}

      {/* タブ */}
      <div style={{ display: 'flex', borderBottom: '2px solid #ddd', marginBottom: 16 }}>
        {tabs.map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            style={{ padding: '8px 16px', border: 'none', borderBottom: activeTab === tab.key ? '2px solid #2b6cb0' : '2px solid transparent', marginBottom: -2, fontWeight: activeTab === tab.key ? 'bold' : 'normal', color: activeTab === tab.key ? '#2b6cb0' : '#666', background: 'none', cursor: 'pointer' }}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'basic' && (
        <table style={{ width: '100%' }}>
          <tbody>
            {[
              ['許可番号', permission.permission_number || '（未採番）'],
              ['申請者氏名', permission.applicant_name],
              ['申請者住所', permission.applicant_address],
              ['使用目的', permission.purpose],
              ['対象財産', property ? `${property.property_code} ${property.name}` : '-'],
              ['使用期間', `${permission.start_date} 〜 ${permission.end_date}`],
              ['使用面積', permission.usage_area_sqm ? `${permission.usage_area_sqm} ㎡` : '-'],
              ['使用料', permission.fee_amount ? `${permission.fee_amount.toLocaleString()} 円` : '-'],
              ['許可年月日', permission.permission_date || '-'],
              ['許可条件', permission.conditions || '-'],
              ['更新連番', `${permission.renewal_seq} 回目`],
              ['登録日時', permission.created_at ? new Date(permission.created_at).toLocaleString('ja-JP') : '-'],
            ].map(([label, value]) => (
              <tr key={label} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '8px 16px', fontWeight: 500, width: 160, background: '#f7fafc' }}>{label}</td>
                <td style={{ padding: 8 }}>{value != null ? String(value) : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {activeTab === 'fee' && (
        <FeeCalculator caseId={parseInt(id)} caseType="permission" permission={permission} />
      )}

      {activeTab === 'files' && (
        <FileList relatedType="permission" relatedId={parseInt(id)} />
      )}

      {activeTab === 'history' && (
        <HistoryList propertyId={parseInt(id)} />
      )}
    </div>
  )
}
