# 03_FUNCTIONAL_REQUIREMENTS.md — Functional Requirements

| Field | Value |
|---|---|
| **Document** | 03_FUNCTIONAL_REQUIREMENTS.md |
| **Version** | 1.0.0 |
| **Author** | SentinelAI Enterprise Architecture Team (Technical Product Owner, Business Analyst, AI Systems Architect) |
| **Purpose** | Enumerate every functional requirement of SentinelAI, organized by module, for direct engineering implementation. |
| **Dependencies** | `docs/01_PRD.md`, `docs/02_SYSTEM_ARCHITECTURE.md` |
| **Status** | Draft — Hackathon Phase 1 |

### Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0.0 | 2026-07-19 | Enterprise Architecture Team | Initial functional requirements set |

### ID Scheme

`FR-<MODULE>-<NNN>` — Priority: `P0` (MVP-blocking), `P1` (high), `P2` (medium), `P3` (future scope).

---

## 1. Dashboard

| ID | Priority | Description | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| FR-DASH-001 | P0 | The AI Dashboard shall display live risk state for every zone across all sites the user has access to. | Dashboard renders current risk score, level (Low/Medium/High/Critical), and zone name within 5s of page load; updates in real time via WebSocket/SSE. | `/api/v1/dashboard`, `/api/v1/risk` |
| FR-DASH-002 | P0 | The AI Dashboard shall surface active alerts prominently, ranked by severity. | Highest-severity unacknowledged alert always appears first; severity uses the same taxonomy as the Alerts module. | FR-ALT-001 |
| FR-DASH-003 | P1 | The AI Dashboard shall show system/agent health status (Vision, Sensor, Risk Engine, Compliance, Emergency, Incident agents). | Each agent shows last-successful-run timestamp and status (Healthy/Degraded/Offline). | `/api/v1/dashboard`, System Monitoring (`docs/02_SYSTEM_ARCHITECTURE.md` §13) |
| FR-DASH-004 | P1 | The AI Dashboard shall allow filtering by site and zone. | Selecting a site/zone filters all dashboard widgets consistently. | FR-DASH-001 |
| FR-DASH-005 | P2 | The AI Dashboard shall display a rationale summary for the current risk score on demand. | Clicking a risk score opens a panel showing contributing Vision/Sensor signals and the Compound Risk Engine's rationale text. | FR-RISK-002 |

## 2. Vision

| ID | Priority | Description | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| FR-VIS-001 | P0 | The Vision Intelligence Agent shall detect PPE violations (missing helmet, vest, gloves) from camera frames. | Detection returns bounding box, class label, confidence score ≥ configurable threshold, and timestamp. | YOLOv8 model, `agents/vision_agent.py` |
| FR-VIS-002 | P0 | The Vision Intelligence Agent shall detect restricted-zone intrusion. | A detected person overlapping a defined restricted polygon within a zone raises an intrusion event within 2s of frame capture. | Zone boundary config (`zones` table) |
| FR-VIS-003 | P1 | The Vision Intelligence Agent shall detect fire/smoke visual indicators. | Detection returns class label `fire` or `smoke` with confidence score and is persisted to `detections`. | YOLOv8 model |
| FR-VIS-004 | P1 | The Vision Intelligence Agent shall detect unsafe machine operation (e.g. missing machine guard, operator in danger zone). | Detection returns class label and zone reference; persisted to `detections`. | Zone/machine config |
| FR-VIS-005 | P0 | All Vision Intelligence Agent detections shall be persisted with the source frame reference, confidence, and timestamp. | Every detection has a row in `detections` with non-null `zone_id`, `confidence`, `created_at`. | `detections` table |
| FR-VIS-006 | P2 | The CCTV Monitoring module shall overlay detection bounding boxes on live/recorded video in the frontend. | Bounding boxes render within 1 frame-refresh cycle of a new detection event. | FR-VIS-001–004, `CctvPage.jsx` |

## 3. Alerts

| ID | Priority | Description | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| FR-ALT-001 | P0 | The system shall generate an alert whenever a risk score crosses a configurable severity threshold. | Alert created in `alerts` table with `severity` (Low/Medium/High/Critical), `zone_id`, `risk_score_id`. | `risk_scores` table |
| FR-ALT-002 | P0 | Alerts shall be delivered to the frontend in real time. | New alert appears in the Alerts module and AI Dashboard within 5s via WebSocket/SSE, no manual refresh required. | FR-DASH-002 |
| FR-ALT-003 | P1 | Users with role `site_operator` or `safety_manager` shall be able to acknowledge an alert. | Acknowledging sets `alerts.acknowledged_by` and `acknowledged_at`; acknowledged alerts move out of the primary unacknowledged view. | RBAC (`docs/02_SYSTEM_ARCHITECTURE.md` §11) |
| FR-ALT-004 | P1 | Critical alerts shall automatically notify the Emergency Response Agent. | An alert with `severity = Critical` triggers an Emergency Response Agent evaluation within 2s of alert creation. | FR-EMR-001 |
| FR-ALT-005 | P2 | Users shall be able to filter the Alerts module by severity, zone, site, and acknowledgment status. | Filter combinations return correct, paginated results from `/api/v1/alerts`. | `/api/v1/alerts` |

## 4. Analytics

| ID | Priority | Description | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| FR-ANL-001 | P1 | The Analytics module shall display historical risk score trends per zone/site over a selectable time range. | Recharts line chart renders correct data for 24h/7d/30d ranges from `/api/v1/analytics`. | `risk_scores` table |
| FR-ANL-002 | P1 | The Analytics module shall display incident frequency by category and zone. | Bar chart aggregates `incidents` by category and zone for the selected time range. | `incidents` table |
| FR-ANL-003 | P2 | The Analytics module shall display compliance posture summary (e.g. open vs. resolved compliance questions/findings). | Summary widget reflects current `compliance_documents`/query history state. | FR-COMP-001 |
| FR-ANL-004 | P2 | The Analytics module shall display agent performance metrics (detection counts, average risk-computation latency). | Metrics sourced from agent run logs; refreshed at least every 5 minutes. | System Monitoring |
| FR-ANL-005 | P3 | Users shall be able to export Analytics views as CSV/PDF. | Export produces a downloadable file matching the on-screen filtered data. | Future Scope |

## 5. Risk Engine

| ID | Priority | Description | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| FR-RISK-001 | P0 | The Compound Risk Engine shall compute a unified risk score by fusing the most recent Vision and Sensor signals for a zone. | Score computed within 3s of the triggering detection/reading; persisted to `risk_scores`. | FR-VIS-005, Sensor readings |
| FR-RISK-002 | P0 | Every risk score shall include a human-readable rationale referencing contributing signals. | `risk_scores.rationale` is non-null and references at least one Vision or Sensor input. | Explainability principle |
| FR-RISK-003 | P1 | The Compound Risk Engine shall classify risk into Low/Medium/High/Critical bands using configurable thresholds. | Band boundaries are configurable per site without a code change. | `backend/core/config.py` |
| FR-RISK-004 | P1 | If Vision signals are unavailable, the Compound Risk Engine shall fall back to Sensor-only scoring and flag reduced confidence. | Fallback scores include `confidence: reduced` and a rationale noting missing Vision input. | Fault Tolerance (`docs/02_SYSTEM_ARCHITECTURE.md` §15) |
| FR-RISK-005 | P2 | Historical risk scores shall remain queryable for Analytics and audit purposes. | `risk_scores` rows are never deleted, only appended. | `docs/ARCHITECTURE_RULES.md` §7 |

## 6. Compliance

| ID | Priority | Description | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| FR-COMP-001 | P0 | The Compliance Copilot shall answer natural-language questions using only ingested regulatory/SOP documents. | Every answer includes at least one citation referencing a `compliance_documents` record. | ChromaDB, `compliance_embeddings` |
| FR-COMP-002 | P0 | If no relevant document is found, the Compliance Copilot shall return an explicit "insufficient information" response rather than fabricating an answer. | No answer is returned without either a citation or the explicit insufficient-information response. | `docs/ARCHITECTURE_RULES.md` §8 |
| FR-COMP-003 | P1 | Users with role `compliance_officer` or `admin` shall be able to ingest new compliance documents. | Uploaded document is chunked, embedded, and stored in ChromaDB with a corresponding `compliance_documents` row within 60s. | RBAC |
| FR-COMP-004 | P2 | The Compliance Copilot shall maintain a query history for audit purposes. | Each query and its answer/citations are logged and retrievable by `compliance_officer`/`admin`. | `audit_logs` table |

## 7. Emergency Response

| ID | Priority | Description | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| FR-EMR-001 | P0 | The Emergency Response Agent shall recommend a protocol when a risk score reaches the Critical band. | Recommendation persisted with reference to the triggering `risk_scores` row and the matched `emergency_protocols` row. | FR-RISK-003, `emergency_protocols` table |
| FR-EMR-002 | P0 | The Emergency Response Agent shall never autonomously actuate physical systems — it recommends only. | No code path in `agents/emergency_agent.py` issues control commands to external systems. | `docs/01_PRD.md` §7 Out of Scope |
| FR-EMR-003 | P1 | Emergency recommendations shall be visible to `site_operator` and `safety_manager` roles immediately upon creation. | Recommendation appears in the AI Dashboard/Alerts view within 5s. | FR-ALT-004 |
| FR-EMR-004 | P2 | The Emergency Response Agent's recommendation shall include the matched protocol's step-by-step instructions. | Recommendation payload includes ordered steps from `emergency_protocols`. | `emergency_protocols` table |

## 8. Reports

| ID | Priority | Description | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| FR-REP-001 | P0 | The Incident Report Generator shall draft a structured incident report whenever an Emergency Response Agent recommendation is created. | Report generated within 30s, persisted to `incidents`, referencing all contributing evidence (detections, readings, risk score). | FR-EMR-001 |
| FR-REP-002 | P1 | Incident reports shall be reviewable and exportable by `safety_manager` and `admin` roles. | Report viewable in the Reports module and exportable (PDF/Markdown) via `/api/v1/incidents`. | RBAC |
| FR-REP-003 | P1 | The Incident Report Generator shall never modify the underlying evidence records it references. | `detections`, `sensor_readings`, and `risk_scores` rows are read-only from the Incident Report Generator's perspective. | `docs/ARCHITECTURE_RULES.md` §8 |
| FR-REP-004 | P2 | Incident reports shall support a manual review/approval workflow before being marked final. | Report has a `status` field (`draft`/`approved`) settable only by `safety_manager`/`admin`. | RBAC |

## 9. Authentication

| ID | Priority | Description | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| FR-AUTH-001 | P0 | Users shall authenticate via `/api/v1/auth/login` using email and password, receiving a JWT access token. | Valid credentials return a signed JWT with role claim; invalid credentials return a 401 with the standard error envelope. | `users` table |
| FR-AUTH-002 | P0 | All endpoints except `/api/v1/auth/login` shall require a valid JWT. | Requests without a valid token receive a 401. | `docs/02_SYSTEM_ARCHITECTURE.md` §11 |
| FR-AUTH-003 | P1 | The system shall support token refresh without requiring re-login. | A valid refresh token exchanges for a new access token via `/api/v1/auth/refresh`. | JWT refresh pattern |
| FR-AUTH-004 | P1 | Access shall be enforced per the five defined roles (`admin`, `safety_manager`, `site_operator`, `compliance_officer`, `viewer`). | Role-restricted endpoints return 403 for unauthorized roles. | `docs/01_PRD.md` §9 |
| FR-AUTH-005 | P2 | Users shall be able to log out, invalidating their refresh token. | Logout revokes the refresh token server-side. | `users` table |

## 10. Administration

| ID | Priority | Description | Acceptance Criteria | Dependencies |
|---|---|---|---|---|
| FR-ADM-001 | P0 | Users with role `admin` shall be able to create, update, and deactivate user accounts. | CRUD operations available via `/api/v1/admin/users` (admin-only); deactivated users cannot authenticate. | RBAC, `users` table |
| FR-ADM-002 | P1 | Users with role `admin` shall be able to manage sites and zones. | CRUD available via `/api/v1/admin/sites`; changes reflected immediately in Dashboard filters (FR-DASH-004). | `sites`, `zones` tables |
| FR-ADM-003 | P1 | Users with role `admin` shall be able to register cameras and sensors and assign them to zones. | CRUD available; new camera/sensor becomes visible to Vision/Sensor agents without a restart. | `cameras`, `sensors` tables |
| FR-ADM-004 | P2 | Users with role `admin` shall be able to configure risk score severity thresholds per site. | Threshold changes apply to subsequent risk computations without a deployment. | FR-RISK-003 |
| FR-ADM-005 | P2 | All administrative actions shall be recorded in the audit log. | Every create/update/deactivate action produces an `audit_logs` row with actor, action, and timestamp. | `audit_logs` table |

---

## Glossary

| Term | Definition |
|---|---|
| FR | Functional Requirement |
| P0–P3 | Priority tiers: P0 MVP-blocking, P1 high, P2 medium, P3 future scope |
| RBAC | Role-Based Access Control |

## References

- `docs/01_PRD.md`, `docs/02_SYSTEM_ARCHITECTURE.md`, `docs/PROJECT_MEMORY.md`, `docs/ARCHITECTURE_RULES.md`

## Assumptions

- `/api/v1/admin/*` sub-routes are introduced as a reasonable extension of the placeholder `/api/v1` list in `docs/PROJECT_MEMORY.md` to support Administration requirements; these should be added to that table in a future update.
- `/api/v1/auth/login`, `/api/v1/auth/refresh` are sub-routes of the existing `/api/v1/auth` placeholder endpoint.

## Future Improvements

- Add non-functional acceptance thresholds (e.g. exact latency SLAs) once real infrastructure benchmarks exist — cross-reference `docs/04_NON_FUNCTIONAL_REQUIREMENTS.md`.
- Expand P3 requirements into full specifications once MVP (P0/P1) is delivered.
