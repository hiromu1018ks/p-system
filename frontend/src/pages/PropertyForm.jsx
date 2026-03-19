import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProperty, createProperty, updateProperty } from '../api/properties'
import PropertyMap from '../components/PropertyMap'

const LAND_CATEGORIES = ['宅地', '田', '畑', '山林', '牧場', '原野', '池沼', '塩田', '鉱泉地', '雑種地', 'その他']

export default function PropertyForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!id

  const [form, setForm] = useState({
    name: '',
    property_type: 'administrative',
    address: '',
    lot_number: '',
    land_category: '',
    area_sqm: '',
    acquisition_date: '',
    latitude: null,
    longitude: null,
    remarks: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isEdit) {
      getProperty(id).then((prop) => {
        setForm({
          name: prop.name,
          property_type: prop.property_type,
          address: prop.address || '',
          lot_number: prop.lot_number || '',
          land_category: prop.land_category || '',
          area_sqm: prop.area_sqm ?? '',
          acquisition_date: prop.acquisition_date || '',
          latitude: prop.latitude,
          longitude: prop.longitude,
          remarks: prop.remarks || '',
        })
      }).catch(() => alert('財産の取得に失敗しました'))
    }
  }, [id, isEdit])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleMapClick = (lat, lng) => {
    setForm((prev) => ({ ...prev, latitude: lat, longitude: lng }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const data = { ...form }
      if (data.area_sqm !== '') data.area_sqm = parseFloat(data.area_sqm)
      else data.area_sqm = null
      if (!data.acquisition_date) data.acquisition_date = null
      if (!data.land_category) data.land_category = null
      if (data.latitude === null) delete data.latitude
      if (data.longitude === null) delete data.longitude

      if (isEdit) {
        const result = await updateProperty(id, data)
        navigate(`/properties/${id}`)
      } else {
        const result = await createProperty(data)
        navigate(`/properties/${result.id}`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <button onClick={() => isEdit ? navigate(`/properties/${id}`) : navigate('/properties')}>
          ← {isEdit ? '詳細に戻る' : '一覧に戻る'}
        </button>
        <h2 style={{ display: 'inline', marginLeft: 12 }}>
          {isEdit ? '財産台帳編集' : '財産台帳新規登録'}
        </h2>
      </div>

      <form onSubmit={handleSubmit}>
        <table style={{ width: '100%', maxWidth: 700 }}>
          <tbody>
            <tr>
              <td style={{ padding: '8px 16px', fontWeight: 500, width: 160, background: '#f7fafc' }}>財産名称 <span style={{ color: 'red' }}>*</span></td>
              <td style={{ padding: 8 }}>
                <input name="name" value={form.name} onChange={handleChange} required style={{ width: '100%' }} />
              </td>
            </tr>
            <tr>
              <td style={{ padding: '8px 16px', fontWeight: 500, background: '#f7fafc' }}>財産区分 <span style={{ color: 'red' }}>*</span></td>
              <td style={{ padding: 8 }}>
                <select name="property_type" value={form.property_type} onChange={handleChange}>
                  <option value="administrative">行政財産</option>
                  <option value="general">普通財産</option>
                </select>
              </td>
            </tr>
            <tr>
              <td style={{ padding: '8px 16px', fontWeight: 500, background: '#f7fafc' }}>所在地</td>
              <td style={{ padding: 8 }}>
                <input name="address" value={form.address} onChange={handleChange} style={{ width: '100%' }} />
              </td>
            </tr>
            <tr>
              <td style={{ padding: '8px 16px', fontWeight: 500, background: '#f7fafc' }}>地番</td>
              <td style={{ padding: 8 }}>
                <input name="lot_number" value={form.lot_number} onChange={handleChange} style={{ width: '100%' }} />
              </td>
            </tr>
            <tr>
              <td style={{ padding: '8px 16px', fontWeight: 500, background: '#f7fafc' }}>地目</td>
              <td style={{ padding: 8 }}>
                <select name="land_category" value={form.land_category} onChange={handleChange}>
                  <option value="">未設定</option>
                  {LAND_CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </td>
            </tr>
            <tr>
              <td style={{ padding: '8px 16px', fontWeight: 500, background: '#f7fafc' }}>面積（㎡）</td>
              <td style={{ padding: 8 }}>
                <input name="area_sqm" type="number" step="0.01" min="0" value={form.area_sqm} onChange={handleChange} />
              </td>
            </tr>
            <tr>
              <td style={{ padding: '8px 16px', fontWeight: 500, background: '#f7fafc' }}>取得年月日</td>
              <td style={{ padding: 8 }}>
                <input name="acquisition_date" type="date" value={form.acquisition_date} onChange={handleChange} />
              </td>
            </tr>
            <tr>
              <td style={{ padding: '8px 16px', fontWeight: 500, background: '#f7fafc' }}>位置情報</td>
              <td style={{ padding: 8 }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                  <input placeholder="緯度" value={form.latitude ?? ''} readOnly style={{ width: 120 }} />
                  <input placeholder="経度" value={form.longitude ?? ''} readOnly style={{ width: 120 }} />
                  {form.latitude != null && (
                    <button type="button" onClick={() => setForm((p) => ({ ...p, latitude: null, longitude: null }))} style={{ fontSize: 12 }}>
                      クリア
                    </button>
                  )}
                </div>
                <p style={{ fontSize: 12, color: '#888', marginBottom: 4 }}>地図をクリックして位置を設定してください</p>
                <PropertyMap latitude={form.latitude} longitude={form.longitude} onMapClick={handleMapClick} editable />
              </td>
            </tr>
            <tr>
              <td style={{ padding: '8px 16px', fontWeight: 500, background: '#f7fafc', verticalAlign: 'top' }}>備考</td>
              <td style={{ padding: 8 }}>
                <textarea name="remarks" value={form.remarks} onChange={handleChange} rows={3} style={{ width: '100%' }} />
              </td>
            </tr>
          </tbody>
        </table>

        {error && <p style={{ color: 'red', marginTop: 8 }}>{error}</p>}

        <div style={{ marginTop: 16 }}>
          <button type="submit" disabled={loading}>
            {loading ? '保存中...' : isEdit ? '更新' : '登録'}
          </button>
          <button type="button" onClick={() => navigate(isEdit ? `/properties/${id}` : '/properties')} style={{ marginLeft: 8, background: '#a0aec0' }}>
            キャンセル
          </button>
        </div>
      </form>
    </div>
  )
}
