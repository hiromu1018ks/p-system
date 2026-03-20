import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProperty, getProperties } from '../api/properties'
import { getLease, createLease, updateLease } from '../api/leases'
import FeeCalculator from '../components/FeeCalculator'

export default function LeaseForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!id

  const [properties, setProperties] = useState([])
  const [form, setForm] = useState({
    property_id: '',
    property_sub_type: 'land',
    lessee_name: '',
    lessee_address: '',
    lessee_contact: '',
    purpose: '',
    start_date: '',
    end_date: '',
    leased_area: '',
    payment_method: 'monthly',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getProperties({ per_page: 100 }).then(d => setProperties(d.items)).catch(() => {})
    if (isEdit) {
      getLease(id).then(l => {
        setForm({
          property_id: l.property_id,
          property_sub_type: l.property_sub_type,
          lessee_name: l.lessee_name,
          lessee_address: l.lessee_address,
          lessee_contact: l.lessee_contact || '',
          purpose: l.purpose,
          start_date: l.start_date,
          end_date: l.end_date,
          leased_area: l.leased_area || '',
          payment_method: l.payment_method || 'monthly',
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
      if (!data.lessee_contact) data.lessee_contact = null
      if (!data.leased_area) data.leased_area = null

      if (isEdit) {
        await updateLease(id, data)
        navigate(`/leases/${id}`)
      } else {
        const result = await createLease(data)
        navigate(`/leases/${result.id}`)
      }
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  const fields = [
    { label: '対象財産', name: 'property_id', required: true, type: 'select', options: properties.map(p => ({ value: p.id, label: `${p.property_code} ${p.name}` })) },
    { label: '財産種別', name: 'property_sub_type', required: true, type: 'select', options: [{ value: 'land', label: '土地' }, { value: 'building', label: '建物' }] },
    { label: '借受者氏名・法人名', name: 'lessee_name', required: true },
    { label: '借受者住所', name: 'lessee_address', required: true },
    { label: '連絡先', name: 'lessee_contact' },
    { label: '貸付目的', name: 'purpose', required: true, type: 'textarea' },
    { label: '開始日', name: 'start_date', required: true, type: 'date' },
    { label: '終了日', name: 'end_date', required: true, type: 'date' },
    { label: '貸付面積・部屋番号', name: 'leased_area' },
    { label: '支払方法', name: 'payment_method', type: 'select', options: [{ value: 'monthly', label: '月払' }, { value: 'semiannual', label: '半期払' }, { value: 'annual', label: '年払' }] },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <button onClick={() => isEdit ? navigate(`/leases/${id}`) : navigate('/leases')}>
          ← {isEdit ? '詳細に戻る' : '一覧に戻る'}
        </button>
        <h2 style={{ display: 'inline', marginLeft: 12 }}>{isEdit ? '貸付案件編集' : '貸付案件 新規登録'}</h2>
      </div>

      <form onSubmit={handleSubmit}>
        <table style={{ width: '100%', maxWidth: 700 }}>
          <tbody>
            {fields.map(({ label, name, required, type = 'text', options }) => (
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
                    <textarea name={name} value={form[name]} onChange={handleChange} rows={3} style={{ width: '100%' }} />
                  ) : (
                    <input name={name} type={type} value={form[name]} onChange={handleChange} required={required} style={{ width: '100%' }} />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {error && <p style={{ color: 'red', marginTop: 8 }}>{error}</p>}

        <div style={{ marginTop: 16 }}>
          <button type="submit" disabled={loading}>{loading ? '保存中...' : isEdit ? '更新' : '登録'}</button>
          <button type="button" onClick={() => navigate(isEdit ? `/leases/${id}` : '/leases')} style={{ marginLeft: 8, background: '#a0aec0' }}>キャンセル</button>
        </div>
      </form>

      {isEdit && (
        <div style={{ marginTop: 24, padding: 16, border: '1px solid #e2e8f0', borderRadius: 4 }}>
          <FeeCalculator caseId={parseInt(id)} caseType="lease" lease={form} />
        </div>
      )}
    </div>
  )
}
