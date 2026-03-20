import { apiClient, setToken, clearToken } from './client'

export async function login(username, password) {
  const data = await apiClient('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  setToken(data.data.access_token)
  return data.data.user
}

export async function logout() {
  const token = sessionStorage.getItem('access_token')
  if (token) {
    await apiClient('/api/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ token }),
    }).catch(() => {})
  }
  clearToken()
}

export async function getMe() {
  const data = await apiClient('/api/auth/me')
  return data.data
}

export function getUsers() { return apiClient('/api/auth/users') }

export function createUser(data) { return apiClient('/api/auth/users', { method: 'POST', body: JSON.stringify(data) }) }

export function unlockUser(userId) { return apiClient(`/api/auth/users/${userId}/unlock`, { method: 'POST' }) }
