import { apiClient } from './client'

export async function generatePermissionPdf(permissionId) {
  const data = await apiClient(`/api/pdf/permission/${permissionId}`, {
    method: 'POST',
  })
  return data.data
}

export async function generateLandLeasePdf(leaseId) {
  const data = await apiClient(`/api/pdf/lease-land/${leaseId}`, {
    method: 'POST',
  })
  return data.data
}

export async function generateBuildingLeasePdf(leaseId) {
  const data = await apiClient(`/api/pdf/lease-building/${leaseId}`, {
    method: 'POST',
  })
  return data.data
}

export async function generateRenewalPdf(caseType, caseId) {
  const data = await apiClient(`/api/pdf/renewal/${caseType}/${caseId}`, {
    method: 'POST',
  })
  return data.data
}

export async function getDocumentHistory(caseType, caseId) {
  const data = await apiClient(`/api/pdf/history/${caseType}/${caseId}`)
  return data.data
}

export async function downloadPdf(documentId) {
  const token = sessionStorage.getItem('access_token')
  const response = await fetch(`/api/pdf/download/${documentId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!response.ok) {
    throw new Error(`PDFのダウンロードに失敗しました: ${response.status}`)
  }

  const contentDisposition = response.headers.get('Content-Disposition')
  let filename = 'document.pdf'
  if (contentDisposition) {
    const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?([^;\s]+)/i)
    if (match) filename = decodeURIComponent(match[1].replace(/"/g, ''))
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}
