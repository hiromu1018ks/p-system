import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProperty, deleteProperty } from '../api/properties'
import PropertyMap from '../components/PropertyMap'
import FileList from '../components/FileList'
import HistoryList from '../components/HistoryList'

export default function PropertyDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [property, setProperty] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('basic')

  useEffect(() => {
    getProperty(id)
      .then(setProperty)
      .catch(() => alert('財産の取得に失敗しました'))
      .finally(() => setLoading(false))
  }, [id])

  const handleDelete = async () => {
    if (!window.confirm(`「${property.name}」を削除しますか？`)) return
    try {
      await deleteProperty(id)
      navigate('/properties')
    } catch (err) {
      alert(err.message)
    }
  }

  if (loading) return <div>読み込み中...</div>
  if (!property) return <div>財産が見つかりません</div>

  const typeLabel = property.property_type === 'administrative' ? '行政財産' : '普通財産'

  const tabs = [
    { key: 'basic', label: '基本情報' },
    { key: 'map', label: '地図' },
    { key: 'files', label: '添付ファイル' },
    { key: 'history', label: '変更履歴' },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <button onClick={() => navigate('/properties')} style={{ marginRight: 12 }}>← 一覧に戻る</button>
          <h2 style={{ display: 'inline' }}>
            {property.property_code} - {property.name}
          </h2>
          <span style={{
            marginLeft: 8, padding: '2px 8px', borderRadius: 4, fontSize: 12,
            background: property.property_type === 'administrative' ? '#bee3f8' : '#c6f6d5',
          }}>
            {typeLabel}
          </span>
        </div>
        <div>
          <button onClick={() => navigate(`/properties/${id}/edit`)} style={{ marginRight: 8 }}>編集</button>
          <button onClick={handleDelete} style={{ background: '#e53e3e' }}>削除</button>
        </div>
      </div>

      <div style={{ display: 'flex', borderBottom: '2px solid #ddd', marginBottom: 16 }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderBottom: activeTab === tab.key ? '2px solid #2b6cb0' : '2px solid transparent',
              marginBottom: '-2px',
              fontWeight: activeTab === tab.key ? 'bold' : 'normal',
              color: activeTab === tab.key ? '#2b6cb0' : '#666',
              background: 'none',
              cursor: 'pointer',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'basic' && (
        <table style={{ width: '100%' }}>
          <tbody>
            {[
              ['財産コード', property.property_code],
              ['財産名称', property.name],
              ['財産区分', typeLabel],
              ['所在地', property.address],
              ['地番', property.lot_number],
              ['地目', property.land_category],
              ['面積（㎡）', property.area_sqm],
              ['取得年月日', property.acquisition_date],
              ['緯度', property.latitude],
              ['経度', property.longitude],
              ['備考', property.remarks],
              ['登録日時', property.created_at ? new Date(property.created_at).toLocaleString('ja-JP') : '-'],
              ['更新日時', property.updated_at ? new Date(property.updated_at).toLocaleString('ja-JP') : '-'],
            ].map(([label, value]) => (
              <tr key={label} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '8px 16px', fontWeight: 500, width: 160, background: '#f7fafc' }}>{label}</td>
                <td style={{ padding: 8 }}>{value != null ? String(value) : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {activeTab === 'map' && (
        <div>
          {property.latitude != null && property.longitude != null ? (
            <PropertyMap latitude={property.latitude} longitude={property.longitude} />
          ) : (
            <p style={{ color: '#888' }}>位置情報が設定されていません。編集画面から設定できます。</p>
          )}
        </div>
      )}

      {activeTab === 'files' && (
        <FileList relatedType="property" relatedId={parseInt(id)} showUpload />
      )}

      {activeTab === 'history' && (
        <HistoryList caseType="property" caseId={parseInt(id)} />
      )}
    </div>
  )
}
