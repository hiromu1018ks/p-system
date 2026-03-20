import { apiClient } from './client'

export async function getDashboardSummary() {
  const data = await apiClient('/api/dashboard/summary')
  return data.data
}
