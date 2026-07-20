import apiClient from './apiClient'

// backend/app/schemas/alerts.py has no PATCH /alerts/{id}/acknowledge route
// yet, so acknowledgements can't be persisted server-side. Track them here
// and re-apply on every fetch so the UI still behaves correctly; this map
// resets on page reload and is superseded once the backend adds the route.
const acknowledgedOverrides = {}

function applyOverrides(item) {
  return {
    ...item,
    rationale: item.message,
    acknowledged_by: acknowledgedOverrides[item.id] ?? item.acknowledged_by,
  }
}

// Mirrors GET /alerts (backend/app/routers/alerts.py)
export async function getAlerts() {
  const { data } = await apiClient.get('/alerts')
  return { ...data, items: data.items.map(applyOverrides) }
}

// No backend route yet (see comment above) — updates the local override map
// so the acknowledged state is reflected immediately and on subsequent fetches.
export async function acknowledgeAlert(id, acknowledgedBy = 'You') {
  acknowledgedOverrides[id] = acknowledgedBy
  return { id, acknowledged_by: acknowledgedBy }
}
