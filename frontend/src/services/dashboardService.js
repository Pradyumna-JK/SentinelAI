import apiClient from './apiClient'

// Mirrors GET /dashboard (backend/app/routers/dashboard.py). A single call
// returns both zone risk summaries and agent health in one payload.
export async function getDashboard() {
  const { data } = await apiClient.get('/dashboard')
  return data
}

// Convenience wrapper for callers that only need zone summaries.
export async function getOverview() {
  const { zones } = await getDashboard()
  return { zones }
}

// Convenience wrapper for callers that only need agent health.
export async function getAgentStatus() {
  const { agents } = await getDashboard()
  return { agents }
}
