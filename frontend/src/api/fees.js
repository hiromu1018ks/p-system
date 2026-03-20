import { apiClient } from './client'

export async function calculateFee(feeData) {
  const data = await apiClient('/api/fees/calculate', {
    method: 'POST',
    body: JSON.stringify(feeData),
  })
  return data.data
}

export async function getFeeDetails(caseType, caseId) {
  const data = await apiClient(`/api/fees/${caseType}/${caseId}`)
  return data.data
}

export async function getUnitPrices(propertyType = null) {
  const query = propertyType ? `?property_type=${propertyType}` : ''
  const data = await apiClient(`/api/unit-prices${query}`)
  return data.data
}

export async function createUnitPrice(unitPriceData) {
  const data = await apiClient('/api/unit-prices', {
    method: 'POST',
    body: JSON.stringify(unitPriceData),
  })
  return data.data
}

export async function updateUnitPrice(id, unitPriceData) {
  const data = await apiClient(`/api/unit-prices/${id}`, {
    method: 'PUT',
    body: JSON.stringify(unitPriceData),
  })
  return data.data
}
