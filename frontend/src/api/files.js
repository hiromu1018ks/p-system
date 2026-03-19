import { getToken } from './client'

export async function uploadFile(relatedType, relatedId, fileType, file) {
  const token = getToken()
  const formData = new FormData()
  formData.append('related_type', relatedType)
  formData.append('related_id', relatedId)
  formData.append('file_type', fileType)
  formData.append('file', file)

  const response = await fetch('/api/files/upload', {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody?.error?.message || `API Error: ${response.status}`)
  }

  const data = await response.json()
  return data.data
}

export async function getFiles(relatedType, relatedId) {
  const response = await fetch(
    `/api/files?related_type=${relatedType}&related_id=${relatedId}`,
    {
      headers: {
        Authorization: `Bearer ${getToken()}`,
      },
    }
  )

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }

  const data = await response.json()
  return data.data
}

export async function downloadFile(fileId) {
  const token = getToken()
  const response = await fetch(`/api/files/${fileId}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`)
  }

  const contentDisposition = response.headers.get('Content-Disposition')
  let filename = 'download'
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

export async function deleteFile(fileId) {
  const token = getToken()
  const response = await fetch(`/api/files/${fileId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody?.error?.message || `API Error: ${response.status}`)
  }

  return response.json()
}
