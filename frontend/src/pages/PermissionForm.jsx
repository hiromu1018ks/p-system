import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProperty, getProperties } from '../api/properties'
import { getPermission, createPermission, updatePermission } from '../api/permissions'
import FeeCalculator from '../components/FeeCalculator'

export default function PermissionForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!id

  const [properties, setProperties] = useState([])
  const [form, setForm] = useState({
    property_id: '',
    applicant_name: '',
    applicant_address: '',
    purpose: '',
    start_date: '',
    end_date: '',
    usage_area_sqm: '',
    conditions: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getProperties({ per_page: 100 }).then(d => setProperties(d.items)).catch(() => {})
    if (isEdit) {
      getPermission(id).then(p => {
        setForm({
          property_id: p.property_id,
          applicant_name: p.applicant_name,
          applicant_address: p.applicant_address,
          purpose: p.purpose,
          start_date: p.start_date,
          end_date: p.end_date,
          usage_area_sqm: p.usage_area_sqm ?? '',
          conditions: p.conditions || '',
        })
      }).catch(() => alert('取得に失敗しました'))
    }
  }, [id, isEdit])

  const handleChange = (e) => setForm(p => ({ ...p, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = { ...form }
      data.property_id = parseInt(data.property_id)
      if (data.usage_area_sqm) data.usage_area_sqm = parseFloat(data.usage_area_sqm)
      else data.usage_area_sqm = null
      if (!data.conditions) data.conditions = null

      if (isEdit) {
        await updatePermission(id, data)
        navigate(`/permissions/${id}`)
      } else {
        const result = await createPermission(data)
        navigate(`/permissions/${result.id}`)
      }
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <button onClick={() => isEdit ? navigate(`/permissions/${id}`) : navigate('/permissions')}>
          ← {isEdit ? '詳細に戻る' : '一覧に戻る'}
        </button>
        <h2 style={{ display: 'inline', marginLeft: 12 }}>{isEdit ? '使用許可案件編集' : '使用許可案件 新規登録'}</h2>
      </div>

      <form onSubmit={handleSubmit}>
        <table style={{ width: '100%', maxWidth: 700 }}>
          <tbody>
            {[
              { label: '対象財産', name: 'property_id', required: true, type: 'select', options: properties.map(p => ({ value: p.id, label: `${p.property_code} ${p.name}` })) },
              { label: '申請者氏名', name: 'applicant_name', required: true },
              { label: '申請者住所', name: 'applicant_address', required: true },
              { label: '使用目的', name: 'purpose', required: true, type: 'textarea' },
              { label: '開始日', name: 'start_date', required: true, type: 'date' },
              { label: '終了日', name: 'end_date', required: true, type: 'date' },
              { label: '使用面積（㎡）', name: 'usage_area_sqm', type: 'number' },
              { label: '許可条件・特記事項', name: 'conditions', type: 'textarea' },
            ].map(({ label, name, required, type = 'text', options, rows }) => (
              <tr key={name}>
                <td style={{ padding: '8px 16px', fontWeight: 500, width: 160, background: '#f7fafc', verticalAlign: type === 'textarea' ? 'top' : undefined }}>
                  {label} {required && <span style={{ color: 'red' }}>*</span>}
                </td>
                <td style={{ padding: 8 }}>
                  {type === 'select' ? (
                    <select name={name} value={form[name]} onChange={handleChange} required style={{ width: '100%' }}>
                      <option value="">選択してください</option>
                      {options?.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                  ) : type === 'textarea' ? (
                    <textarea name={name} value={form[name]} onChange={handleChange} rows={rows || 3} style={{ width: '100%' }} />
                  ) : (
                    <input name={name} type={type} value={form[name]} onChange={handleChange} required={required} step={type === 'number' ? '0.01' : undefined} style={{ width: '100%' }} />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {error && <p style={{ color: 'red', marginTop: 8 }}>{error}</p>}

        <div style={{ marginTop: 16 }}>
          <button type="submit" disabled={loading}>{loading ? '保存中...' : isEdit ? '更新' : '登録'}</button>
          <button type="button" onClick={() => navigate(isEdit ? `/permissions/${id}` : '/permissions')} style={{ marginLeft: 8, background: '#a0aec0' }}>キャンセル</button>
        </div>
      </form>

      {/* 登録済みの場合は料金計算を表示（編集画面のみ） */}
      {isEdit && (
        <div style={{ marginTop: 24, padding: 16, border: '1px solid #e2e8f0', borderRadius: 4 }}>
          <FeeCalculator caseId={parseInt(id)} caseType="permission" />
        </div>
      )}
    </div>
  )
}
