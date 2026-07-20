# 08_API_SPECIFICATION.md — API Specification

| Field | Value |
|---|---|
| **Document** | 08_API_SPECIFICATION.md |
| **Version** | 1.0.0 |
| **Author** | SentinelAI Enterprise Engineering Team (Senior API Architect, Principal Backend Architect) |
| **Purpose** | Document every REST endpoint of SentinelAI for direct backend/frontend implementation. |
| **Dependencies** | `docs/07_DATABASE_DESIGN.md`, `docs/03_FUNCTIONAL_REQUIREMENTS.md`, `docs/CODING_STANDARDS.md` |
| **Status** | Draft — Hackathon Phase 2 |

### Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0.0 | 2026-07-19 | Enterprise Engineering Team | Initial complete API specification |

---

## 1. Global Conventions

Referenced by every endpoint below instead of being repeated per-entry.

**Base URL**: `/api/v1`

**Standard Headers** (all authenticated requests):
```
Content-Type: application/json
Authorization: Bearer <jwt_access_token>
```

**Standard Response Envelope** (per `docs/CODING_STANDARDS.md` §6):
```json
{ "success": true, "data": { }, "error": null }
```
```json
{ "success": false, "data": null, "error": { "code": "STRING_CODE", "message": "Human readable message" } }
```

**Standard Status Codes**: `200` OK, `201` Created, `204` No Content, `400` Bad Request, `401` Unauthorized (missing/invalid JWT), `403` Forbidden (role not permitted), `404` Not Found, `422` Validation Error, `429` Too Many Requests, `500` Internal Server Error.

**Standard Rate Limits**:
| Tier | Limit | Applies to |
|---|---|---|
| Standard | 120 requests/min per user | Read (`GET`) endpoints |
| Write | 60 requests/min per user | `POST`/`PATCH`/`PUT`/`DELETE` endpoints |
| Ingestion | 300 requests/min per API key | Agent-internal ingestion endpoints (Vision/Sensor) |
| Auth | 10 requests/min per IP | `/api/v1/auth/*` (brute-force protection) |

**Standard Pagination** (list endpoints): query params `page` (default 1), `limit` (default 25, max 100); response includes `data.items[]` and `data.pagination: { page, limit, total, total_pages }`.

**Authentication**: all endpoints require a valid JWT bearer token except `POST /api/v1/auth/login`. Role enforcement uses the five roles from `docs/PROJECT_MEMORY.md` §14: `admin`, `safety_manager`, `site_operator`, `compliance_officer`, `viewer`.

---

## 2. Authentication

### `POST /api/v1/auth/login`

**Purpose**: Authenticate a user and issue access/refresh tokens (FR-AUTH-001).
**Auth**: None.
**Headers**: `Content-Type: application/json`.
**Request Body**:
```json
{ "email": "priya@sentinelai.demo", "password": "••••••••" }
```
**Response Body (200)**:
```json
{ "success": true, "data": { "access_token": "eyJ...", "refresh_token": "eyJ...", "user": { "id": "uuid", "email": "priya@sentinelai.demo", "role": "safety_manager" } }, "error": null }
```
**Status Codes**: 200, 400, 401, 422.
**Validation**: `email` valid format, `password` non-empty.
**Error Responses**: `401 { "error": { "code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect" } }`.
**Rate Limiting**: Auth tier (10/min/IP).
**Implementation Notes**: Passwords verified via bcrypt/argon2 hash comparison (never plaintext, per NFR-SEC-005).

### `POST /api/v1/auth/refresh`

**Purpose**: Exchange a valid refresh token for a new access token (FR-AUTH-003).
**Auth**: Refresh token in body (not bearer header).
**Request Body**: `{ "refresh_token": "eyJ..." }`
**Response Body (200)**: `{ "success": true, "data": { "access_token": "eyJ..." }, "error": null }`
**Status Codes**: 200, 401.
**Error Responses**: `401 { "error": { "code": "INVALID_REFRESH_TOKEN", "message": "Refresh token is invalid or expired" } }`.
**Rate Limiting**: Auth tier.

### `POST /api/v1/auth/logout`

**Purpose**: Revoke the current refresh token (FR-AUTH-005).
**Auth**: Bearer JWT required (any role).
**Response Body (204)**: no content.
**Status Codes**: 204, 401.
**Rate Limiting**: Write tier.

---

## 3. Dashboard

### `GET /api/v1/dashboard/overview`

**Purpose**: Return live risk state across all zones the user can access (FR-DASH-001).
**Auth**: Bearer JWT (all roles).
**Query Params**: `site_id` (optional), `zone_id` (optional) — FR-DASH-004.
**Response Body (200)**:
```json
{ "success": true, "data": { "zones": [ { "zone_id": "uuid", "zone_name": "Loading Dock A", "risk_score": 72.5, "risk_level": "High", "active_alerts": 2 } ] }, "error": null }
```
**Status Codes**: 200, 401, 422 (invalid filter).
**Rate Limiting**: Standard tier.
**Implementation Notes**: Backed by the latest `risk_scores` row per zone; real-time updates pushed separately via WebSocket (see `docs/06_SYSTEM_WORKFLOW.md` §5).

### `GET /api/v1/dashboard/status`

**Purpose**: Return AI agent health/heartbeat status (FR-DASH-003).
**Auth**: Bearer JWT (all roles).
**Response Body (200)**:
```json
{ "success": true, "data": { "agents": [ { "name": "vision_intelligence_agent", "status": "Healthy", "last_run_at": "2026-07-19T10:15:03Z" } ] }, "error": null }
```
**Status Codes**: 200, 401.
**Rate Limiting**: Standard tier.

---

## 4. Vision (includes CCTV Monitoring)

### `GET /api/v1/vision/detections`

**Purpose**: List/filter Vision Intelligence Agent detections (FR-VIS-006).
**Auth**: Bearer JWT (all roles).
**Query Params**: `zone_id`, `camera_id`, `class_label`, `from`, `to`, `page`, `limit`.
**Response Body (200)**:
```json
{ "success": true, "data": { "items": [ { "id": "uuid", "camera_id": "uuid", "zone_id": "uuid", "class_label": "ppe_violation", "confidence": 0.94, "bounding_box": {"x":120,"y":80,"width":60,"height":140}, "created_at": "2026-07-19T10:15:03Z" } ], "pagination": { "page": 1, "limit": 25, "total": 132, "total_pages": 6 } }, "error": null }
```
**Status Codes**: 200, 401, 422.
**Rate Limiting**: Standard tier.

### `POST /api/v1/vision/detections`

**Purpose**: Internal ingestion endpoint used by the Vision Intelligence Agent to persist a detection (FR-VIS-005).
**Auth**: Service-to-service API key (agent identity), not a user JWT.
**Request Body**:
```json
{ "camera_id": "uuid", "zone_id": "uuid", "class_label": "fire", "confidence": 0.88, "bounding_box": {"x":10,"y":20,"width":200,"height":150}, "frame_reference": "frames/.../000456.jpg" }
```
**Response Body (201)**: `{ "success": true, "data": { "id": "uuid" }, "error": null }`
**Status Codes**: 201, 401, 422.
**Validation**: `confidence` between 0–1; `class_label` in allowed enum.
**Rate Limiting**: Ingestion tier.
**Implementation Notes**: Not exposed to the frontend; called only by `agents/vision_agent.py` via the backend service layer, per `docs/ARCHITECTURE_RULES.md` §5 (agents never call each other or the frontend directly).

### `GET /api/v1/vision/detections/{id}`

**Purpose**: Retrieve a single detection with full evidence detail.
**Auth**: Bearer JWT (all roles).
**Response Body (200)**: single detection object (see above).
**Status Codes**: 200, 401, 404.
**Rate Limiting**: Standard tier.

### `GET /api/v1/cctv/streams`

**Purpose**: List active camera streams for the CCTV Monitoring page (FR-VIS-006, owned by Vision Intelligence Agent per `docs/PROJECT_MEMORY.md` §6).
**Auth**: Bearer JWT (all roles).
**Query Params**: `zone_id` (optional).
**Response Body (200)**:
```json
{ "success": true, "data": { "streams": [ { "camera_id": "uuid", "zone_id": "uuid", "name": "Dock A - North", "stream_url": "https://.../hls/cam1.m3u8", "status": "active" } ] }, "error": null }
```
**Status Codes**: 200, 401.
**Rate Limiting**: Standard tier.

---

## 5. Sensors

### `GET /api/v1/sensors/readings`

**Purpose**: List/filter Sensor Intelligence Agent readings (analogous to Vision detections, §4).
**Auth**: Bearer JWT (all roles).
**Query Params**: `zone_id`, `sensor_id`, `type` (`gas`|`temperature`|`vibration`|`pressure`), `from`, `to`, `page`, `limit`.
**Response Body (200)**:
```json
{ "success": true, "data": { "items": [ { "id": "uuid", "sensor_id": "uuid", "zone_id": "uuid", "value": 42.0, "unit": "ppm", "is_anomaly": true, "created_at": "2026-07-19T10:15:00Z" } ], "pagination": { "page": 1, "limit": 25, "total": 88, "total_pages": 4 } }, "error": null }
```
**Status Codes**: 200, 401, 422.
**Rate Limiting**: Standard tier.

### `POST /api/v1/sensors/readings`

**Purpose**: Internal ingestion endpoint used by the Sensor Intelligence Agent to persist a reading (mirrors `POST /api/v1/vision/detections`, §4).
**Auth**: Service-to-service API key (agent identity), not a user JWT.
**Request Body**:
```json
{ "sensor_id": "uuid", "zone_id": "uuid", "type": "gas", "value": 42.0, "unit": "ppm" }
```
**Response Body (201)**: `{ "success": true, "data": { "id": "uuid", "is_anomaly": true }, "error": null }`
**Status Codes**: 201, 401, 422.
**Validation**: `value` numeric; `type` in allowed enum (`gas`,`temperature`,`vibration`,`pressure`).
**Rate Limiting**: Ingestion tier.
**Implementation Notes**: Not exposed to the frontend; called only by `agents/sensor_agent.py` via the backend service layer, per `docs/ARCHITECTURE_RULES.md` §5. Anomaly flag computed against the sensor's configured baseline range (`docs/11_AI_ARCHITECTURE.md` §2).

### `GET /api/v1/sensors/readings/{id}`

**Purpose**: Retrieve a single sensor reading with full detail.
**Auth**: Bearer JWT (all roles).
**Status Codes**: 200, 401, 404.
**Rate Limiting**: Standard tier.

---

## 6. Alerts

### `GET /api/v1/alerts`

**Purpose**: List/filter alerts (FR-ALT-005).
**Auth**: Bearer JWT (all roles).
**Query Params**: `severity`, `zone_id`, `site_id`, `acknowledged` (bool), `page`, `limit`.
**Response Body (200)**:
```json
{ "success": true, "data": { "items": [ { "id": "uuid", "zone_id": "uuid", "risk_score_id": "uuid", "severity": "Critical", "acknowledged_by": null, "created_at": "2026-07-19T10:15:05Z" } ], "pagination": { "page": 1, "limit": 25, "total": 4, "total_pages": 1 } }, "error": null }
```
**Status Codes**: 200, 401, 422.
**Rate Limiting**: Standard tier.

### `PATCH /api/v1/alerts/{id}/acknowledge`

**Purpose**: Acknowledge an alert (FR-ALT-003).
**Auth**: Bearer JWT, roles `site_operator`, `safety_manager`, `admin`.
**Response Body (200)**: `{ "success": true, "data": { "id": "uuid", "acknowledged_by": "uuid", "acknowledged_at": "2026-07-19T10:16:00Z" }, "error": null }`
**Status Codes**: 200, 401, 403, 404.
**Error Responses**: `403 { "error": { "code": "ROLE_NOT_PERMITTED", "message": "Role viewer cannot acknowledge alerts" } }`.
**Rate Limiting**: Write tier.

---

## 7. Analytics

### `GET /api/v1/analytics/risk-trends`

**Purpose**: Historical risk score trends (FR-ANL-001).
**Auth**: Bearer JWT (all roles).
**Query Params**: `zone_id`, `site_id`, `range` (`24h`|`7d`|`30d`).
**Response Body (200)**:
```json
{ "success": true, "data": { "points": [ { "timestamp": "2026-07-19T00:00:00Z", "avg_score": 22.4 } ] }, "error": null }
```
**Status Codes**: 200, 401, 422.
**Rate Limiting**: Standard tier.

### `GET /api/v1/analytics/incident-frequency`

**Purpose**: Incident frequency by category/zone (FR-ANL-002).
**Auth**: Bearer JWT (all roles).
**Response Body (200)**: `{ "success": true, "data": { "buckets": [ { "zone_id": "uuid", "category": "fire", "count": 3 } ] }, "error": null }`
**Status Codes**: 200, 401.
**Rate Limiting**: Standard tier.

### `GET /api/v1/analytics/compliance-summary`

**Purpose**: Compliance posture summary (FR-ANL-003).
**Auth**: Bearer JWT (all roles).
**Response Body (200)**: `{ "success": true, "data": { "documents_ingested": 12, "queries_last_30d": 48, "insufficient_info_rate": 0.04 }, "error": null }`
**Status Codes**: 200, 401.
**Rate Limiting**: Standard tier.

---

## 8. Risk Engine

### `GET /api/v1/risk/scores`

**Purpose**: List/filter compound risk scores (FR-RISK-005).
**Auth**: Bearer JWT (all roles).
**Query Params**: `zone_id`, `level`, `from`, `to`, `page`, `limit`.
**Response Body (200)**: paginated list of `risk_scores` rows (see `docs/07_DATABASE_DESIGN.md` §5.8).
**Status Codes**: 200, 401, 422.
**Rate Limiting**: Standard tier.

### `GET /api/v1/risk/scores/{id}`

**Purpose**: Retrieve a single risk score with full rationale (FR-DASH-005, FR-RISK-002).
**Auth**: Bearer JWT (all roles).
**Response Body (200)**:
```json
{ "success": true, "data": { "id": "uuid", "zone_id": "uuid", "score": 82.0, "level": "High", "rationale": "Elevated due to PPE violation (conf. 0.94) correlated with gas sensor reading 40% above baseline.", "confidence": "full", "contributing_detection_ids": ["uuid"], "contributing_reading_ids": ["uuid"], "created_at": "2026-07-19T10:15:04Z" }, "error": null }
```
**Status Codes**: 200, 401, 404.
**Rate Limiting**: Standard tier.

### `GET /api/v1/risk/scores/latest`

**Purpose**: Get the most recent risk score for a zone (used by AI Dashboard polling fallback).
**Auth**: Bearer JWT (all roles).
**Query Params**: `zone_id` (required).
**Status Codes**: 200, 401, 404, 422.
**Rate Limiting**: Standard tier.

---

## 9. Compliance

### `POST /api/v1/compliance/query`

**Purpose**: Ask the Compliance Copilot a natural-language question (FR-COMP-001/002).
**Auth**: Bearer JWT (all roles).
**Request Body**: `{ "question": "What PPE is required in a high-noise zone under OSHA 1910.95?" }`
**Response Body (200 — answer found)**:
```json
{ "success": true, "data": { "answer": "Hearing protection is required when noise exceeds 85 dBA TWA...", "citations": [ { "document_id": "uuid", "title": "OSHA 1910.95", "chunk_index": 4 } ], "insufficient_info": false }, "error": null }
```
**Response Body (200 — no relevant document)**:
```json
{ "success": true, "data": { "answer": null, "citations": [], "insufficient_info": true }, "error": null }
```
**Status Codes**: 200, 401, 422.
**Validation**: `question` non-empty, max 2000 chars.
**Rate Limiting**: Standard tier (LLM cost-sensitive — consider a stricter 20/min override in production, see `docs/13_CONFIGURATION.md`).
**Implementation Notes**: Every query/answer pair logged to `audit_logs` (`action: compliance.query`) per FR-COMP-004.

### `POST /api/v1/compliance/documents`

**Purpose**: Ingest a new compliance document (FR-COMP-003).
**Auth**: Bearer JWT, roles `compliance_officer`, `admin`.
**Request Body**: `multipart/form-data` — `file`, `title`.
**Response Body (201)**: `{ "success": true, "data": { "id": "uuid", "title": "OSHA 1910.95", "version": 1 }, "error": null }`
**Status Codes**: 201, 401, 403, 422.
**Validation**: file type in (`pdf`, `docx`, `txt`, `md`); max 25MB.
**Rate Limiting**: Write tier.
**Implementation Notes**: Triggers chunking + embedding pipeline into ChromaDB; `compliance_embeddings` rows created asynchronously, complete within 60s (FR-COMP-003).

### `GET /api/v1/compliance/documents`

**Purpose**: List ingested compliance documents.
**Auth**: Bearer JWT (all roles).
**Status Codes**: 200, 401.
**Rate Limiting**: Standard tier.

### `GET /api/v1/compliance/queries`

**Purpose**: Retrieve Compliance Copilot query history (FR-COMP-004).
**Auth**: Bearer JWT, roles `compliance_officer`, `admin`.
**Status Codes**: 200, 401, 403.
**Rate Limiting**: Standard tier.

---

## 10. Emergency

### `GET /api/v1/emergency/recommendations`

**Purpose**: List Emergency Response Agent recommendations (FR-EMR-003).
**Auth**: Bearer JWT (all roles).
**Query Params**: `zone_id`, `from`, `to`.
**Response Body (200)**: paginated list of `emergency_recommendations` rows (`docs/07_DATABASE_DESIGN.md` §5.11).
**Status Codes**: 200, 401.
**Rate Limiting**: Standard tier.

### `GET /api/v1/emergency/protocols`

**Purpose**: List configured emergency protocols for a site.
**Auth**: Bearer JWT (all roles).
**Query Params**: `site_id`, `hazard_type`.
**Status Codes**: 200, 401.
**Rate Limiting**: Standard tier.

### `POST /api/v1/emergency/protocols`

**Purpose**: Create/configure an emergency protocol (supports FR-EMR-001 matching).
**Auth**: Bearer JWT, roles `safety_manager`, `admin`.
**Request Body**: `{ "site_id": "uuid", "hazard_type": "fire", "title": "Fire Evacuation - Zone A", "steps": ["Sound alarm", "Evacuate via exit B", "Call site emergency line"] }`
**Response Body (201)**: created protocol object.
**Status Codes**: 201, 401, 403, 422.
**Rate Limiting**: Write tier.

---

## 11. Reports

### `GET /api/v1/incidents`

**Purpose**: List/filter incident reports (FR-REP-002).
**Auth**: Bearer JWT, roles `safety_manager`, `admin`, `viewer` (read-only).
**Query Params**: `status`, `zone_id`, `from`, `to`, `page`, `limit`.
**Status Codes**: 200, 401, 403, 422.
**Rate Limiting**: Standard tier.

### `GET /api/v1/incidents/{id}`

**Purpose**: Retrieve a single incident report with full evidence chain.
**Auth**: Bearer JWT, roles `safety_manager`, `admin`, `viewer`.
**Status Codes**: 200, 401, 403, 404.
**Rate Limiting**: Standard tier.

### `PATCH /api/v1/incidents/{id}/approve`

**Purpose**: Approve a draft incident report (FR-REP-004).
**Auth**: Bearer JWT, roles `safety_manager`, `admin`.
**Response Body (200)**: `{ "success": true, "data": { "id": "uuid", "status": "approved", "approved_by": "uuid" }, "error": null }`
**Status Codes**: 200, 401, 403, 404, 409 (already approved).
**Rate Limiting**: Write tier.

### `GET /api/v1/incidents/{id}/export`

**Purpose**: Export an approved incident report as PDF/Markdown (FR-REP-002).
**Auth**: Bearer JWT, roles `safety_manager`, `admin`, `viewer`.
**Query Params**: `format` (`pdf`|`md`).
**Status Codes**: 200, 401, 403, 404, 409 (draft not yet approved).
**Rate Limiting**: Standard tier.

---

## 12. Administration

### `GET /api/v1/admin/users` / `POST /api/v1/admin/users`

**Purpose**: List/create user accounts (FR-ADM-001).
**Auth**: Bearer JWT, role `admin` only.
**Request Body (POST)**: `{ "email": "marcus@sentinelai.demo", "full_name": "Marcus Lee", "role": "site_operator", "password": "••••••••" }`
**Status Codes**: 200/201, 401, 403, 422.
**Rate Limiting**: Write tier (POST) / Standard tier (GET).

### `PATCH /api/v1/admin/users/{id}`

**Purpose**: Update or deactivate a user account (FR-ADM-001).
**Auth**: Bearer JWT, role `admin` only.
**Request Body**: `{ "is_active": false }` or `{ "role": "safety_manager" }`
**Status Codes**: 200, 401, 403, 404, 422.
**Rate Limiting**: Write tier.

### `GET /api/v1/admin/sites` / `POST /api/v1/admin/sites`

**Purpose**: List/create sites and zones (FR-ADM-002).
**Auth**: Bearer JWT, role `admin` only.
**Status Codes**: 200/201, 401, 403, 422.
**Rate Limiting**: Write tier (POST) / Standard tier (GET).

### `GET /api/v1/admin/cameras` / `POST /api/v1/admin/cameras`

**Purpose**: List/register cameras, assign to zones (FR-ADM-003).
**Auth**: Bearer JWT, role `admin` only.
**Status Codes**: 200/201, 401, 403, 422.
**Rate Limiting**: Write tier (POST) / Standard tier (GET).

### `GET /api/v1/admin/sensors` / `POST /api/v1/admin/sensors`

**Purpose**: List/register sensors, assign to zones (FR-ADM-003).
**Auth**: Bearer JWT, role `admin` only.
**Status Codes**: 200/201, 401, 403, 422.
**Rate Limiting**: Write tier (POST) / Standard tier (GET).

---

## 13. Appendix — System Endpoints

### `GET /api/v1/health`

**Purpose**: Report backend, database, and vector store connectivity (`docs/02_SYSTEM_ARCHITECTURE.md` §13, NFR-MON-001).
**Auth**: None (unauthenticated, used by uptime monitors).
**Response Body (200)**:
```json
{ "success": true, "data": { "backend": "ok", "database": "ok", "vector_store": "ok" }, "error": null }
```
**Status Codes**: 200, 503 (any dependency down).
**Rate Limiting**: Exempt.

---

## Glossary

| Term | Definition |
|---|---|
| Envelope | Standard `{success, data, error}` JSON response shape |
| Ingestion endpoint | Service-to-service endpoint called by an agent, not the frontend |

## References

- `docs/07_DATABASE_DESIGN.md`, `docs/03_FUNCTIONAL_REQUIREMENTS.md`, `docs/CODING_STANDARDS.md`

## Assumptions

- `/api/v1/vision/detections` (POST) and `/api/v1/sensors/readings` (POST, see `docs/11_AI_ARCHITECTURE.md`) are agent-internal, API-key-authenticated ingestion routes rather than user-facing endpoints; this distinction was not explicit upstream and is documented here as the authoritative decision.
- `/api/v1/admin/*` and `/api/v1/health` are formalized here consistent with their introduction in `docs/PROJECT_MEMORY.md` v1.1.0.

## Future Improvements

- Add OpenAPI/Swagger auto-generation from FastAPI route definitions once implementation begins, replacing this hand-authored spec as the live reference.
- Add stricter, cost-aware rate limiting for `/api/v1/compliance/query` once real OpenAI API usage costs are measured.
