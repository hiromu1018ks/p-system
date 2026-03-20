import { apiClient, getToken } from './client'

export async function getPermissions(params = {}) {
  const query = new URLSearchParams()
  if (params.status) query.set('status', params.status)
  if (params.q) query.set('q', params.q)
  if (params.page) query.set('page', params.page)
  if (params.per_page) query.set('per_page', params.per_page)
  const qs = query.toString()
  const data = await apiClient(`/api/permissions${qs ? '?' + qs : ''}`)
  return data.data
}

export async function getPermission(id) {
  const data = await apiClient(`/api/permissions/${id}`)
  return data.data
}

export async function createPermission(permissionData) {
  const data = await apiClient('/api/permissions', {
    method: 'POST',
    body: JSON.stringify(permissionData),
  })
  return data.data
}

export async function updatePermission(id, permissionData) {
  const data = await apiClient(`/api/permissions/${id}`, {
    method: 'PUT',
    body: JSON.stringify(permissionData),
  })
  return data.data
}

export async function deletePermission(id) {
  const data = await apiClient(`/api/permissions/${id}`, { method: 'DELETE' })
  return data.data
}

export async function changePermissionStatus(id, statusChange) {
  const data = await apiClient(`/api/permissions/${id}/status`, {
    method: 'POST',
    body: JSON.stringify(statusChange),
  })
  return data.data
}

export async function startRenewal(id, reason = '') {
  const data = await apiClient(`/api/permissions/${id}/renewal`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
  return data.data
}

export async function getPermissionHistory(id) {
  const data = await apiClient(`/api/permissions/${id}/history`)
  return data.data
}

export async function exportPermissions(status) {
  const params = status ? `?status=${status}` : '';
  const token = getToken();
  const res = await fetch(`/api/export/permissions${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('エクスポートに失敗しました');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = '使用許可案件.csv';
  a.click();
  URL.revokeObjectURL(url);
}
