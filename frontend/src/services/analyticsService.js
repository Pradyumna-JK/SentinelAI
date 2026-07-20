import { mockDelay } from './apiClient'
import { mockRiskTrend, mockIncidentFrequency, mockComplianceSummary } from '../data/mockData'

// Mirrors GET /api/v1/analytics/risk-trends (docs/08_API_SPECIFICATION.md §7)
export function getRiskTrends() {
  return mockDelay({ points: mockRiskTrend })
}

// Mirrors GET /api/v1/analytics/incident-frequency
export function getIncidentFrequency() {
  return mockDelay({ buckets: mockIncidentFrequency })
}

// Mirrors GET /api/v1/analytics/compliance-summary
export function getComplianceSummary() {
  return mockDelay(mockComplianceSummary)
}
