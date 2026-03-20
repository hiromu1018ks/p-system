import { useState } from 'react'
import { calculateFee } from '../api/fees'

function formatYen(amount) {
  if (amount == null) return '-'
  return amount.toLocaleString() + ' 円'
}

export default function FeeCalculator({ caseId, caseType, permission, onFeeCalculated }) {
  const [form, setForm] = useState({
    unit_price: '',
    area_sqm: permission?.usage_area_sqm || '',
    start_date: permission?.start_date || '',
    end_date: permission?.end_date || '',
    discount_rate: 0,
    tax_rate: 0.10,
    discount_reason: '',
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: name === 'discount_rate' || name === 'tax_rate' ? parseFloat(value) || 0 : value }))
  }

  const handleCalculate = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const data = await calculateFee({
        case_id: caseId,
        case_type: caseType,
        unit_price: parseInt(form.unit_price),
        area_sqm: parseFloat(form.area_sqm),
        start_date: form.start_date,
        end_date: form.end_date,
        discount_rate: form.discount_rate,
        tax_rate: form.tax_rate,
        discount_reason: form.discount_reason || null,
      })
      setResult(data)
      if (onFeeCalculated) onFeeCalculated(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h4 style={{ marginBottom: 8 }}>使用料計算</h4>
      <form onSubmit={handleCalculate} style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'flex-end' }}>
        <div>
          <label style={{ fontSize: 12 }}>単価（円/㎡/月）</label>
          <input name="unit_price" type="number" value={form.unit_price} onChange={handleChange} required style={{ width: 120, display: 'block' }} />
        </div>
        <div>
          <label style={{ fontSize: 12 }}>面積（㎡）</label>
          <input name="area_sqm" type="number" step="0.01" value={form.area_sqm} onChange={handleChange} required style={{ width: 100, display: 'block' }} />
        </div>
        <div>
          <label style={{ fontSize: 12 }}>開始日</label>
          <input name="start_date" type="date" value={form.start_date} onChange={handleChange} required style={{ display: 'block' }} />
        </div>
        <div>
          <label style={{ fontSize: 12 }}>終了日</label>
          <input name="end_date" type="date" value={form.end_date} onChange={handleChange} required style={{ display: 'block' }} />
        </div>
        <div>
          <label style={{ fontSize: 12 }}>減額率（%）</label>
          <input name="discount_rate" type="number" step="0.01" min="0" max="100" value={form.discount_rate * 100} onChange={(e) => setForm(p => ({ ...p, discount_rate: parseFloat(e.target.value) / 100 || 0 }))} style={{ width: 80, display: 'block' }} />
        </div>
        <div>
          <label style={{ fontSize: 12 }}>課税</label>
          <select name="tax_rate" value={form.tax_rate} onChange={handleChange} style={{ display: 'block' }}>
            <option value={0.10}>課税 10%</option>
            <option value={0.08}>課税 8%</option>
            <option value={0}>非課税</option>
          </select>
        </div>
        <button type="submit" disabled={loading} style={{ padding: '6px 16px' }}>
          {loading ? '計算中...' : '計算'}
        </button>
      </form>

      {form.discount_rate > 0 && (
        <div style={{ marginTop: 4 }}>
          <input name="discount_reason" placeholder="減免理由" value={form.discount_reason} onChange={handleChange} style={{ width: 300, fontSize: 13 }} />
        </div>
      )}

      {error && <p style={{ color: 'red', marginTop: 8 }}>{error}</p>}

      {result && (
        <div style={{ marginTop: 12, padding: 12, background: '#f7fafc', borderRadius: 4, fontSize: 13, fontFamily: 'monospace' }}>
          <div>【使用料 計算内訳】</div>
          <div>  単価         : {formatYen(result.unit_price)}/{result.area_sqm} ㎡/月</div>
          <div>  面積         :  {result.area_sqm} ㎡</div>
          <div>  使用期間     :  {result.months}ヶ月 + {result.fraction_days}日（{result.start_date} 〜 {result.end_date}）</div>
          <div>  基本料金     :  {formatYen(result.base_amount)}</div>
          {result.fraction_amount > 0 && <div>  日割調整     :  {formatYen(result.fraction_amount)}</div>}
          <div>  小計         :  {formatYen(result.subtotal)}</div>
          {result.discount_rate > 0 && (
            <>
              <div>  減額（{(result.discount_rate * 100).toFixed(0)}%）: -{formatYen(result.subtotal - result.discounted_amount)}{result.discount_reason ? `（${result.discount_reason}）` : ''}</div>
            </>
          )}
          <div>  税抜金額     :  {formatYen(result.discounted_amount)}</div>
          {result.tax_amount > 0 && <div>  消費税（{(result.tax_rate * 100).toFixed(0)}%）: {formatYen(result.tax_amount)}</div>}
          <div style={{ borderTop: '1px solid #cbd5e0', marginTop: 4, paddingTop: 4, fontWeight: 'bold' }}>
            税込合計     :  {formatYen(result.total_amount)}
          </div>
        </div>
      )}
    </div>
  )
}
