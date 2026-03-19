function getToken() {
  return sessionStorage.getItem('access_token')
}

function setToken(token) {
  sessionStorage.setItem('access_token', token)
}

function clearToken() {
  sessionStorage.removeItem('access_token')
}

async function apiClient(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(path, { ...options, headers })

  if (response.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('認証エラー')
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody?.error?.message || `API Error: ${response.status}`)
  }

  return response.json()
}

export { apiClient, setToken, clearToken, getToken }
