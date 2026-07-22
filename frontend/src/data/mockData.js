// Dummy JSON fixtures for SentinelAI frontend placeholder pages.
// Shapes loosely mirror docs/08_API_SPECIFICATION.md response envelopes so that
// wiring real endpoints later is a drop-in replacement for these services.

export const mockDetections = [
  { id: 'd1', camera_id: 'c1', zone_id: 'z1', class_label: 'ppe_violation', confidence: 0.94, created_at: '2026-07-19T10:14:40Z' },
  { id: 'd2', camera_id: 'c3', zone_id: 'z2', class_label: 'fire', confidence: 0.88, created_at: '2026-07-19T10:11:02Z' },
  { id: 'd3', camera_id: 'c5', zone_id: 'z3', class_label: 'intrusion', confidence: 0.77, created_at: '2026-07-19T09:55:18Z' },
]

export const mockComplianceDocuments = [
  { id: 'doc1', title: 'OSHA 1910.95 - Occupational Noise Exposure', version: 1, uploaded_by: 'Dana Ruiz', created_at: '2026-07-10T00:00:00Z' },
  { id: 'doc2', title: 'OSHA 1910.132 - General PPE Requirements', version: 2, uploaded_by: 'Dana Ruiz', created_at: '2026-07-08T00:00:00Z' },
  { id: 'doc3', title: 'Site SOP - Confined Space Entry', version: 1, uploaded_by: 'Dana Ruiz', created_at: '2026-06-29T00:00:00Z' },
]

export const mockChatMessages = [
  { id: 'm1', role: 'assistant', text: 'Hi, I’m the SentinelAI Compliance Copilot. Ask me anything about your ingested regulations and SOPs.', citations: [] },
  { id: 'm2', role: 'user', text: 'What PPE is required in a high-noise zone under OSHA 1910.95?', citations: [] },
  { id: 'm3', role: 'assistant', text: 'Hearing protection is required whenever an 8-hour time-weighted average exceeds 85 dBA. Employers must provide protectors and enforce use above 90 dBA.', citations: [{ document_id: 'doc1', title: 'OSHA 1910.95', chunk_index: 4 }] },
]

export const mockRiskTrend = [
  { timestamp: '07/13', avg_score: 24 },
  { timestamp: '07/14', avg_score: 31 },
  { timestamp: '07/15', avg_score: 28 },
  { timestamp: '07/16', avg_score: 45 },
  { timestamp: '07/17', avg_score: 39 },
  { timestamp: '07/18', avg_score: 52 },
  { timestamp: '07/19', avg_score: 61 },
]

export const mockIncidentFrequency = [
  { category: 'PPE Violation', count: 12 },
  { category: 'Fire / Smoke', count: 3 },
  { category: 'Intrusion', count: 7 },
  { category: 'Gas Anomaly', count: 5 },
  { category: 'Unsafe Operation', count: 4 },
]

export const mockComplianceSummary = {
  documents_ingested: 3,
  queries_last_30d: 48,
  insufficient_info_rate: 0.04,
}

export const mockUsers = [
  { id: 'u1', full_name: 'Alex Chen', email: 'alex@sentinelai.demo', role: 'admin', is_active: true },
  { id: 'u2', full_name: 'Priya Shah', email: 'priya@sentinelai.demo', role: 'safety_manager', is_active: true },
  { id: 'u3', full_name: 'Marcus Lee', email: 'marcus@sentinelai.demo', role: 'site_operator', is_active: true },
  { id: 'u4', full_name: 'Dana Ruiz', email: 'dana@sentinelai.demo', role: 'compliance_officer', is_active: true },
  { id: 'u5', full_name: 'Jordan Blake', email: 'jordan@sentinelai.demo', role: 'viewer', is_active: false },
]

export const mockSites = [
  { id: 's1', name: 'Riverside Plant', address: '400 Riverside Way, Akron, OH', zones: 3 },
  { id: 's2', name: 'Northgate Facility', address: '12 Northgate Blvd, Dayton, OH', zones: 3 },
]
