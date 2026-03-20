import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { getLeases, bulkPreviewFee, bulkUpdateFee } from '../api/leases'

const buttonStyle = {
  padding: '8px 16px',
  background: '#2b6cb0',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '14px',
}

const buttonDisabledStyle = {
  ...buttonStyle,
  opacity: 0.6,
  cursor: 'not-allowed',
}

const secondaryButtonStyle = {
  ...buttonStyle,
  background: '#718096',
}

const inputStyle = {
  padding: '8px 12px',
  border: '1px solid #ccc',
  borderRadius: '4px',
  fontSize: '14px',
}

const STEPS = ['対象選択', 'パラメータ設定', 'プレビュー確認']

export default function BulkFeeUpdate() {
  const { user } = useAuth()
  const [step, setStep] = useState(1)
  const [selectedIds, setSelectedIds] = useState([])
  const [params, setParams] = useState({
    new_unit_price: '',
    discount_rate: '0',
    tax_rate: '0.10',
    discount_reason: '',
  })
  const [previewResult, setPreviewResult] = useState(null)
  const [updateResult, setUpdateResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (user?.role !== 'admin') {
    return <p>管理者のみアクセス可能です。</p>
  }

  const reset = () => {
    setStep(1)
    setSelectedIds([])
    setParams({
      new_unit_price: '',
      discount_rate: '0',
      tax_rate: '0.10',
      discount_reason: '',
    })
    setPreviewResult(null)
    setUpdateResult(null)
    setLoading(false)
    setError('')
  }

  return (
    <div>
      <h2 style={{ marginBottom: 16 }}>一括賃料改定</h2>

      {/* Step indicator */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 24, borderBottom: '2px solid #ddd' }}>
        {STEPS.map((label, i) => {
          const stepNum = i + 1
          return (
            <button
              key={stepNum}
              onClick={() => {
                if (stepNum < step) setStep(stepNum)
              }}
              disabled={stepNum > step}
              style={{
                padding: '10px 20px',
                border: 'none',
                background: 'none',
                cursor: stepNum < step ? 'pointer' : 'default',
                fontSize: '14px',
                fontWeight: stepNum === step ? 'bold' : 'normal',
                color: stepNum <= step ? '#2b6cb0' : '#999',
                borderBottom: stepNum === step ? '2px solid #2b6cb0' : '2px solid transparent',
                marginBottom: '-2px',
              }}
            >
              ステップ{stepNum}：{label}
            </button>
          )
        })}
      </div>

      {error && (
        <div style={{ padding: '12px 16px', background: '#fff5f5', border: '1px solid #e53e3e', borderRadius: 4, marginBottom: 16, color: '#c53030' }}>
          {error}
        </div>
      )}

      {step === 1 && (
        <Step1Select
          selectedIds={selectedIds}
          setSelectedIds={setSelectedIds}
          onNext={() => { setError(''); setStep(2) }}
          buttonStyle={buttonStyle}
          buttonDisabledStyle={buttonDisabledStyle}
        />
      )}

      {step === 2 && (
        <Step2Params
          params={params}
          setParams={setParams}
          onPreview={async () => {
            setError('')
            setLoading(true)
            setPreviewResult(null)
            try {
              const body = {
                lease_ids: selectedIds,
                new_unit_price: parseFloat(params.new_unit_price),
                discount_rate: parseFloat(params.discount_rate) || 0,
                tax_rate: parseFloat(params.tax_rate) || 0,
                discount_reason: params.discount_reason || null,
              }
              const res = await bulkPreviewFee(body)
              setPreviewResult(res.data)
              setStep(3)
            } catch (err) {
              setError(err.message || 'プレビューの取得に失敗しました。')
            } finally {
              setLoading(false)
            }
          }}
          onBack={() => setStep(1)}
          loading={loading}
          buttonStyle={buttonStyle}
          buttonDisabledStyle={buttonDisabledStyle}
          secondaryButtonStyle={secondaryButtonStyle}
          inputStyle={inputStyle}
        />
      )}

      {step === 3 && previewResult && (
        <Step3Preview
          previewResult={previewResult}
          onExecute={async () => {
            setError('')
            setLoading(true)
            setUpdateResult(null)
            try {
              const body = {
                lease_ids: selectedIds,
                new_unit_price: parseFloat(params.new_unit_price),
                discount_rate: parseFloat(params.discount_rate) || 0,
                tax_rate: parseFloat(params.tax_rate) || 0,
                discount_reason: params.discount_reason || null,
              }
              const res = await bulkUpdateFee(body)
              setUpdateResult(res.data)
            } catch (err) {
              setError(err.message || '一括更新に失敗しました。')
            } finally {
              setLoading(false)
            }
          }}
          onBack={() => setStep(2)}
          loading={loading}
          buttonStyle={buttonStyle}
          buttonDisabledStyle={buttonDisabledStyle}
          secondaryButtonStyle={secondaryButtonStyle}
        />
      )}

      {updateResult && (
        <div style={{
          padding: 24,
          background: '#f0fff4',
          border: '1px solid #38a169',
          borderRadius: 8,
          textAlign: 'center',
        }}>
          <h3 style={{ color: '#276749', marginBottom: 8 }}>一括賃料改定が完了しました</h3>
          <p style={{ marginBottom: 16 }}>{updateResult.updated_count}件の賃料を更新しました。</p>
          <button style={buttonStyle} onClick={reset}>新しく実行する</button>
        </div>
      )}
    </div>
  )
}

function Step1Select({ selectedIds, setSelectedIds, onNext, buttonStyle, buttonDisabledStyle }) {
  const [leases, setLeases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const data = await getLeases({ status: 'active', per_page: 100 })
        setLeases(data.items || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const toggleAll = () => {
    if (selectedIds.length === leases.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(leases.map(l => l.id))
    }
  }

  const toggleOne = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  if (loading) return <p>読み込み中...</p>
  if (error) return <p style={{ color: '#e53e3e' }}>{error}</p>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <p>
          対象となる有効な貸付案件から賃料を一括改定する対象を選択してください。
        </p>
        <span style={{ fontWeight: 'bold', color: '#2b6cb0' }}>
          {selectedIds.length}件選択中
        </span>
      </div>

      {leases.length === 0 ? (
        <p>有効な貸付案件がありません。</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 16 }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: 8, textAlign: 'center', width: 40 }}>
                <input
                  type="checkbox"
                  checked={selectedIds.length === leases.length && leases.length > 0}
                  onChange={toggleAll}
                />
              </th>
              <th style={{ padding: 8, textAlign: 'left' }}>貸付番号</th>
              <th style={{ padding: 8, textAlign: 'left' }}>財産名</th>
              <th style={{ padding: 8, textAlign: 'left' }}>借受人名</th>
              <th style={{ padding: 8, textAlign: 'right' }}>現在年間賃料</th>
            </tr>
          </thead>
          <tbody>
            {leases.map(lease => (
              <tr key={lease.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: 8, textAlign: 'center' }}>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(lease.id)}
                    onChange={() => toggleOne(lease.id)}
                  />
                </td>
                <td style={{ padding: 8 }}>{lease.lease_number}</td>
                <td style={{ padding: 8 }}>{lease.property_name || '-'}</td>
                <td style={{ padding: 8 }}>{lease.lessee_name}</td>
                <td style={{ padding: 8, textAlign: 'right' }}>
                  {lease.annual_rent != null ? lease.annual_rent.toLocaleString() + '円' : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ textAlign: 'right' }}>
        <button
          style={selectedIds.length === 0 ? buttonDisabledStyle : buttonStyle}
          disabled={selectedIds.length === 0}
          onClick={onNext}
        >
          次へ
        </button>
      </div>
    </div>
  )
}

function Step2Params({ params, setParams, onPreview, onBack, loading, buttonStyle, buttonDisabledStyle, secondaryButtonStyle, inputStyle }) {
  const updateField = (key, value) => {
    setParams(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div>
      <p style={{ marginBottom: 16 }}>改定後の賃料計算パラメータを入力してください。</p>

      <div style={{
        background: '#f8f9fa',
        padding: 16,
        borderRadius: 8,
        marginBottom: 16,
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: 12,
        alignItems: 'end',
      }}>
        <div>
          <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>
            新単価（円/㎡）
          </label>
          <input
            type="number"
            value={params.new_unit_price}
            onChange={e => updateField('new_unit_price', e.target.value)}
            placeholder="0"
            min="0"
            style={{ ...inputStyle, width: '100%' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>
            減免率
          </label>
          <input
            type="number"
            value={params.discount_rate}
            onChange={e => updateField('discount_rate', e.target.value)}
            placeholder="0"
            min="0"
            max="1"
            step="0.01"
            style={{ ...inputStyle, width: '100%' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>
            消費税率
          </label>
          <input
            type="number"
            value={params.tax_rate}
            onChange={e => updateField('tax_rate', e.target.value)}
            placeholder="0.10"
            min="0"
            max="1"
            step="0.01"
            style={{ ...inputStyle, width: '100%' }}
          />
        </div>
        <div style={{ gridColumn: '1 / -1' }}>
          <label style={{ display: 'block', marginBottom: 4, fontSize: 13, fontWeight: 'bold' }}>
            減免事由（任意）
          </label>
          <input
            type="text"
            value={params.discount_reason}
            onChange={e => updateField('discount_reason', e.target.value)}
            placeholder="減免事由を入力"
            style={{ ...inputStyle, width: '100%' }}
          />
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button style={secondaryButtonStyle} onClick={onBack}>
          戻る
        </button>
        <button
          style={!params.new_unit_price || loading ? buttonDisabledStyle : buttonStyle}
          disabled={!params.new_unit_price || loading}
          onClick={onPreview}
        >
          {loading ? 'プレビュー中...' : 'プレビュー'}
        </button>
      </div>
    </div>
  )
}

function Step3Preview({ previewResult, onExecute, onBack, loading, buttonStyle, buttonDisabledStyle, secondaryButtonStyle }) {
  const items = previewResult.items || []

  return (
    <div>
      <p style={{ marginBottom: 16 }}>
        以下のプレビューを確認し、「実行」ボタンで賃料を一括更新します。
      </p>

      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 16 }}>
        <thead>
          <tr style={{ borderBottom: '2px solid #ddd' }}>
            <th style={{ padding: 8, textAlign: 'left' }}>貸付番号</th>
            <th style={{ padding: 8, textAlign: 'left' }}>財産名</th>
            <th style={{ padding: 8, textAlign: 'left' }}>借受人名</th>
            <th style={{ padding: 8, textAlign: 'right' }}>現在年間賃料</th>
            <th style={{ padding: 8, textAlign: 'right' }}>改定後年間賃料</th>
          </tr>
        </thead>
        <tbody>
          {items.map(item => (
            <tr key={item.lease_id} style={{ borderBottom: '1px solid #eee' }}>
              <td style={{ padding: 8 }}>{item.lease_number}</td>
              <td style={{ padding: 8 }}>{item.property_name || '-'}</td>
              <td style={{ padding: 8 }}>{item.lessee_name}</td>
              <td style={{ padding: 8, textAlign: 'right' }}>
                {item.current_annual_rent != null ? item.current_annual_rent.toLocaleString() + '円' : '-'}
              </td>
              <td style={{ padding: 8, textAlign: 'right', fontWeight: 'bold', color: '#2b6cb0' }}>
                {item.new_total_amount != null ? item.new_total_amount.toLocaleString() + '円' : '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p style={{ marginBottom: 16, fontWeight: 'bold' }}>
        合計：{previewResult.count}件
      </p>

      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button style={secondaryButtonStyle} onClick={onBack}>
          戻る
        </button>
        <button
          style={loading ? buttonDisabledStyle : { ...buttonStyle, background: '#e53e3e' }}
          disabled={loading}
          onClick={() => {
            if (window.confirm(`${previewResult.count}件の賃料を一括更新します。よろしいですか？`)) {
              onExecute()
            }
          }}
        >
          {loading ? '更新中...' : '実行'}
        </button>
      </div>
    </div>
  )
}
