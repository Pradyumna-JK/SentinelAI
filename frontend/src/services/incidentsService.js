import { mockDelay } from './apiClient'
import { mockIncidents } from '../data/mockData'

let incidents = [...mockIncidents]

// Mirrors GET /api/v1/incidents (docs/08_API_SPECIFICATION.md §11)
export function getIncidents() {
  return mockDelay({ items: incidents })
}

// Mirrors PATCH /api/v1/incidents/{id}/approve
export function approveIncident(id) {
  incidents = incidents.map((i) => (i.id === id ? { ...i, status: 'approved' } : i))
  return mockDelay({ id, status: 'approved' }, 300)
}
