import apiClient from './apiClient'

// backend/app/schemas/alerts.py's field is `message`; AlertCard.jsx renders
// `rationale` — kept as a display-only rename here rather than touching
// that component's prop name.
function toDisplayAlert(item) {
  return { ...item, rationale: item.message }
}

// Mirrors GET /alerts (backend/app/api/alerts.py)
export async function getAlerts() {
  const { data } = await apiClient.get('/alerts')
  return { ...data, items: data.items.map(toDisplayAlert) }
}

// Mirrors POST /alerts/{id}/acknowledge — acknowledged_by is resolved
// server-side from the caller's own auth token, not passed by the client.
export async function acknowledgeAlert(id) {
  const { data } = await apiClient.post(`/alerts/${id}/acknowledge`)
  return toDisplayAlert(data)
}
