import { apiClient } from './client'

export async function getLeases(params = {}) {
  const query = new URLSearchParams()
  if (params.status) query.set('status', params.status)
  if (params.q) query.set('q', params.q)
  if (params.page) query.set('page', params.page)
  if (params.per_page) query.set('per_page', params.per_page)
  const qs = query.toString()
  const data = await apiClient(`/api/leases${qs ? '?' + qs : ''}`)
  return data.data
}

export async function getLease(id) {
  const data = await apiClient(`/api/leases/${id}`)
  return data.data
}

export async function createLease(leaseData) {
  const data = await apiClient('/api/leases', {
    method: 'POST',
    body: JSON.stringify(leaseData),
  })
  return data.data
}

export async function updateLease(id, leaseData) {
  const data = await apiClient(`/api/leases/${id}`, {
    method: 'PUT',
    body: JSON.stringify(leaseData),
  })
  return data.data
}

export async function deleteLease(id) {
  const data = await apiClient(`/api/leases/${id}`, { method: 'DELETE' })
  return data.data
}

export async function changeLeaseStatus(id, statusChange) {
  const data = await apiClient(`/api/leases/${id}/status`, {
    method: 'POST',
    body: JSON.stringify(statusChange),
  })
  return data.data
}

export async function startLeaseRenewal(id, reason = '') {
  const data = await apiClient(`/api/leases/${id}/renewal`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
  return data.data
}

export async function getLeaseHistory(id) {
  const data = await apiClient(`/api/leases/${id}/history`)
  return data.data
}
