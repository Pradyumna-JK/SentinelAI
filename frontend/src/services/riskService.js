import apiClient from './apiClient'

// Mirrors GET /risk (backend/app/routers/risk.py)
export async function getRiskScores() {
  const { data } = await apiClient.get('/risk')
  return data
}
