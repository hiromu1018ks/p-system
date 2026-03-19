import { apiClient } from './client'

export async function getProperties(params = {}) {
  const query = new URLSearchParams()
  if (params.q) query.set('q', params.q)
  if (params.type) query.set('type', params.type)
  if (params.page) query.set('page', params.page)
  if (params.per_page) query.set('per_page', params.per_page)

  const qs = query.toString()
  const data = await apiClient(`/api/properties${qs ? '?' + qs : ''}`)
  return data.data
}

export async function getProperty(id) {
  const data = await apiClient(`/api/properties/${id}`)
  return data.data
}

export async function createProperty(propertyData) {
  const data = await apiClient('/api/properties', {
    method: 'POST',
    body: JSON.stringify(propertyData),
  })
  return data.data
}

export async function updateProperty(id, propertyData) {
  const data = await apiClient(`/api/properties/${id}`, {
    method: 'PUT',
    body: JSON.stringify(propertyData),
  })
  return data.data
}

export async function deleteProperty(id) {
  const data = await apiClient(`/api/properties/${id}`, {
    method: 'DELETE',
  })
  return data.data
}

export async function getPropertyHistory(id) {
  const data = await apiClient(`/api/properties/${id}/history`)
  return data.data
}
