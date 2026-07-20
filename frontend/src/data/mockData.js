// Dummy JSON fixtures for SentinelAI frontend placeholder pages.
// Shapes loosely mirror docs/08_API_SPECIFICATION.md response envelopes so that
// wiring real endpoints later is a drop-in replacement for these services.

export const mockZones = [
  { zone_id: 'z1', zone_name: 'Loading Dock A', site_name: 'Riverside Plant', risk_score: 78, risk_level: 'High', active_alerts: 2 },
  { zone_id: 'z2', zone_name: 'Furnace Bay 2', site_name: 'Riverside Plant', risk_score: 92, risk_level: 'Critical', active_alerts: 1 },
  { zone_id: 'z3', zone_name: 'Assembly Line 3', site_name: 'Riverside Plant', risk_score: 34, risk_level: 'Medium', active_alerts: 0 },
  { zone_id: 'z4', zone_name: 'Warehouse North', site_name: 'Northgate Facility', risk_score: 12, risk_level: 'Low', active_alerts: 0 },
  { zone_id: 'z5', zone_name: 'Chemical Storage', site_name: 'Northgate Facility', risk_score: 55, risk_level: 'Medium', active_alerts: 1 },
  { zone_id: 'z6', zone_name: 'Loading Dock B', site_name: 'Northgate Facility', risk_score: 8, risk_level: 'Low', active_alerts: 0 },
]

export const mockAgentStatus = [
  { name: 'Vision Intelligence Agent', status: 'Healthy', last_run_at: '2026-07-19T10:15:03Z' },
  { name: 'Sensor Intelligence Agent', status: 'Healthy', last_run_at: '2026-07-19T10:15:01Z' },
  { name: 'Compound Risk Engine', status: 'Healthy', last_run_at: '2026-07-19T10:15:04Z' },
  { name: 'Compliance Copilot', status: 'Healthy', last_run_at: '2026-07-19T10:12:40Z' },
  { name: 'Emergency Response Agent', status: 'Degraded', last_run_at: '2026-07-19T09:58:12Z' },
  { name: 'Incident Report Generator', status: 'Healthy', last_run_at: '2026-07-19T10:01:22Z' },
]

export const mockCameras = [
  { camera_id: 'c1', zone_id: 'z1', name: 'Dock A - North', status: 'active', stream_url: null },
  { camera_id: 'c2', zone_id: 'z1', name: 'Dock A - South', status: 'active', stream_url: null },
  { camera_id: 'c3', zone_id: 'z2', name: 'Furnace Bay 2 - Overview', status: 'active', stream_url: null },
  { camera_id: 'c4', zone_id: 'z2', name: 'Furnace Bay 2 - Entry', status: 'offline', stream_url: null },
  { camera_id: 'c5', zone_id: 'z3', name: 'Assembly Line 3 - East', status: 'active', stream_url: null },
  { camera_id: 'c6', zone_id: 'z5', name: 'Chemical Storage - Rack 4', status: 'active', stream_url: null },
]

export const mockDetections = [
  { id: 'd1', camera_id: 'c1', zone_id: 'z1', class_label: 'ppe_violation', confidence: 0.94, created_at: '2026-07-19T10:14:40Z' },
  { id: 'd2', camera_id: 'c3', zone_id: 'z2', class_label: 'fire', confidence: 0.88, created_at: '2026-07-19T10:11:02Z' },
  { id: 'd3', camera_id: 'c5', zone_id: 'z3', class_label: 'intrusion', confidence: 0.77, created_at: '2026-07-19T09:55:18Z' },
]

export const mockAlerts = [
  { id: 'a1', zone_name: 'Furnace Bay 2', severity: 'Critical', rationale: 'Fire detected (conf. 0.88) correlated with temperature sensor 46% above baseline.', acknowledged_by: null, created_at: '2026-07-19T10:11:05Z' },
  { id: 'a2', zone_name: 'Loading Dock A', severity: 'High', rationale: 'PPE violation (conf. 0.94) detected — missing hard hat in active work zone.', acknowledged_by: null, created_at: '2026-07-19T10:14:42Z' },
  { id: 'a3', zone_name: 'Chemical Storage', severity: 'Medium', rationale: 'Gas sensor reading 22% above baseline, no correlated visual signal.', acknowledged_by: 'Priya Shah', created_at: '2026-07-19T09:40:11Z' },
  { id: 'a4', zone_name: 'Assembly Line 3', severity: 'Low', rationale: 'Brief restricted-zone boundary touch, self-resolved within 4s.', acknowledged_by: 'Marcus Lee', created_at: '2026-07-19T08:55:30Z' },
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

export const mockIncidents = [
  { id: 'i1', title: 'Fire Detection - Furnace Bay 2', zone_name: 'Furnace Bay 2', status: 'draft', severity: 'Critical', created_at: '2026-07-19T10:11:30Z' },
  { id: 'i2', title: 'PPE Violation - Loading Dock A', zone_name: 'Loading Dock A', status: 'approved', severity: 'High', created_at: '2026-07-18T14:22:10Z' },
  { id: 'i3', title: 'Gas Anomaly - Chemical Storage', zone_name: 'Chemical Storage', status: 'approved', severity: 'Medium', created_at: '2026-07-17T09:03:44Z' },
  { id: 'i4', title: 'Restricted Zone Touch - Assembly Line 3', zone_name: 'Assembly Line 3', status: 'approved', severity: 'Low', created_at: '2026-07-15T16:41:02Z' },
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

export const currentUser = { full_name: 'Priya Shah', role: 'safety_manager' }
