import { mockDelay } from './apiClient'
import { mockUsers, mockSites } from '../data/mockData'

// Mirrors GET /api/v1/admin/users (docs/08_API_SPECIFICATION.md §12)
export function getUsers() {
  return mockDelay({ items: mockUsers })
}

// Mirrors GET /api/v1/admin/sites
export function getSites() {
  return mockDelay({ items: mockSites })
}
