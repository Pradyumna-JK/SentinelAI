import apiClient from './apiClient'

// Mirrors GET /incidents (backend/app/api/incidents.py)
export async function getIncidents() {
  const { data } = await apiClient.get('/incidents')
  return data
}

// Mirrors POST /incidents/{id}/approve
export async function approveIncident(id) {
  const { data } = await apiClient.post(`/incidents/${id}/approve`)
  return data
}

// Mirrors POST /incidents/{id}/close
export async function closeIncident(id) {
  const { data } = await apiClient.post(`/incidents/${id}/close`)
  return data
}
