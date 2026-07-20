# 09_FRONTEND_SPECIFICATION.md — Frontend Specification

| Field | Value |
|---|---|
| **Document** | 09_FRONTEND_SPECIFICATION.md |
| **Version** | 1.0.0 |
| **Author** | SentinelAI Enterprise Engineering Team (Principal Frontend Architect, UX Architect) |
| **Purpose** | Serve as the frontend developer's handbook — every page, its components, data contracts, and states. |
| **Dependencies** | `docs/08_API_SPECIFICATION.md`, `docs/10_COMPONENT_LIBRARY.md`, `docs/02_SYSTEM_ARCHITECTURE.md` §5 |
| **Status** | Draft — Hackathon Phase 3 |

### Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0.0 | 2026-07-19 | Enterprise Engineering Team | Initial frontend specification, 8 pages |

### Page ↔ Component Naming

Per `docs/02_SYSTEM_ARCHITECTURE.md` §5, page component filenames are frozen. This document's page titles map to them as follows:

| Page Title (this doc) | Component File | Route |
|---|---|---|
| Dashboard | `DashboardPage.jsx` | `/dashboard` |
| Camera Monitoring | `CctvPage.jsx` | `/cctv` |
| Alert Center | `AlertsPage.jsx` | `/alerts` |
| Compliance Copilot | `CompliancePage.jsx` | `/compliance` |
| Incident Reports | `IncidentsPage.jsx` | `/incidents` |
| Analytics | `AnalyticsPage.jsx` | `/analytics` |
| Settings | `AdminPage.jsx` | `/settings` |
| Login | `LoginPage.jsx` | `/login` |

All pages except Login require an authenticated session; role-gated sections are noted per page.

---

## 1. Dashboard

**Purpose**: Unified live view of risk state, active alerts, and system health (FR-DASH-001–005).

**Wireframe Description**: Top bar with site/zone filter selector. Left two-thirds: a zone risk grid (`RiskMeter` cards per zone, color-coded by level). Right third: an `AlertCard` stack showing the highest-severity unacknowledged alerts first. Bottom strip: agent health `StatusBadge` row (Vision, Sensor, Risk, Compliance, Emergency, Incident).

**Components**: `RiskMeter`, `AlertCard`, `StatusBadge`, `Card`, `Chart` (sparkline variant, mini sparkline per zone), site/zone `Sidebar` filter, `Navbar`.

**Cards**: One risk card per zone (score, level, active alert count). **Tables**: none (card-based). **Charts**: mini sparkline per zone card (Recharts). **Buttons**: "Acknowledge" on each `AlertCard`. **Forms**: none. **Modals**: risk rationale detail modal (FR-DASH-005), opened from a risk card.

**Navigation**: Default landing page post-login for all roles; primary nav item "Dashboard".

**Responsive Behavior**: Risk grid reflows from a 3-column layout (desktop) to 1-column stacked (mobile); alert stack collapses under the risk grid below 768px.

**Accessibility**: Risk level color coding paired with text labels (not color alone), per NFR-ACC-001; all cards keyboard-focusable and activatable via Enter (NFR-ACC-002).

**Expected API Calls**: `GET /api/v1/dashboard/overview`, `GET /api/v1/dashboard/status`, WebSocket subscription for live updates (`docs/06_SYSTEM_WORKFLOW.md` §5).

**Expected JSON**: see `docs/08_API_SPECIFICATION.md` §3.

**Loading State**: skeleton `RiskMeter` cards (`LoadingSkeleton`) while `overview` loads.

**Empty State**: "No zones configured for your account yet" with a CTA to Settings (for `admin`) or a contact-admin message (other roles).

**Error State**: `Toast` notification + inline retry button if `overview`/`status` calls fail; last-known-good data remains visible with a "stale" badge.

**Acceptance Criteria**: matches FR-DASH-001–005 acceptance criteria in `docs/03_FUNCTIONAL_REQUIREMENTS.md` §1.

---

## 2. Camera Monitoring

**Purpose**: Live/recorded CCTV feeds with in-frame AI detection overlays (FR-VIS-006).

**Wireframe Description**: Grid of `CameraTile` components (responsive grid, 1–4 columns based on viewport), each showing a live stream with bounding-box overlays for recent detections. Selecting a tile expands to a focused single-stream view with a detection `Timeline` beneath it.

**Components**: `CameraTile`, `Timeline`, `StatusBadge` (camera online/offline), `Modal` (expanded view), zone filter `Sidebar`.

**Cards**: `CameraTile` acts as the card unit. **Tables**: detection log table in expanded view (timestamp, class, confidence). **Charts**: none. **Buttons**: expand/collapse, mute/unmute (if audio present). **Forms**: none. **Modals**: expanded single-camera view.

**Navigation**: Primary nav item "Camera Monitoring"; accessible to all roles (read-only for `viewer`).

**Responsive Behavior**: Grid columns reduce from 4→2→1 as viewport narrows; expanded view is full-screen on mobile.

**Accessibility**: Each `CameraTile` has an `aria-label` describing zone/camera name and current status; detection overlays include a text-equivalent list in the expanded view for screen readers.

**Expected API Calls**: `GET /api/v1/cctv/streams`, `GET /api/v1/vision/detections?camera_id=...` (expanded view).

**Expected JSON**: see `docs/08_API_SPECIFICATION.md` §4.

**Loading State**: `LoadingSkeleton` tiles while streams list loads; per-tile spinner while the video stream buffers.

**Empty State**: "No cameras registered for this zone" (links to Settings for `admin`).

**Error State**: offline `StatusBadge` on the tile plus a "Feed unavailable" placeholder image if a stream fails to connect.

**Acceptance Criteria**: bounding boxes render within one frame-refresh cycle of a new detection event (FR-VIS-006).

---

## 3. Alert Center

**Purpose**: Real-time, severity-ranked alert management (FR-ALT-001–005).

**Wireframe Description**: Filterable list of `AlertCard` items (severity, zone, site, acknowledgment status filters in a top toolbar), sorted by severity then recency. Each card expands inline to show the triggering risk score rationale.

**Components**: `AlertCard`, `StatusBadge`, `Table` (compact list view toggle), filter controls, `Toast` (new-alert notification).

**Cards**: `AlertCard` per alert. **Tables**: optional dense table view for power users. **Charts**: none. **Buttons**: "Acknowledge", "View Risk Detail". **Forms**: filter form (severity/zone/site/status). **Modals**: none (inline expansion preferred over modal for alerts).

**Navigation**: Primary nav item "Alerts"; badge count of unacknowledged Critical/High alerts shown in `Navbar`.

**Responsive Behavior**: Filter toolbar collapses into a `Modal`-based filter sheet on mobile.

**Accessibility**: New alerts announced via an `aria-live="polite"` region; severity conveyed via icon + text, not color alone.

**Expected API Calls**: `GET /api/v1/alerts`, `PATCH /api/v1/alerts/{id}/acknowledge`, WebSocket subscription for new alerts.

**Expected JSON**: see `docs/08_API_SPECIFICATION.md` §6.

**Loading State**: `LoadingSkeleton` list rows.

**Empty State**: "No active alerts — all clear" with a calm/positive visual treatment.

**Error State**: acknowledge action failure shows an inline `Toast` and reverts the optimistic UI update.

**Acceptance Criteria**: acknowledgment updates `alerts.acknowledged_by`/`acknowledged_at` and moves the alert out of the primary unacknowledged view (FR-ALT-003).

---

## 4. Compliance Copilot

**Purpose**: RAG-based natural-language Q&A over ingested regulations/SOPs (FR-COMP-001–004).

**Wireframe Description**: Chat-style interface (`ChatWindow`) on the left two-thirds; a right-hand panel listing ingested `compliance_documents` with an "Upload Document" action (role-gated). Each answer bubble shows inline citation chips linking to the source document.

**Components**: `ChatWindow`, `Card` (document list item), citation chip (variant of `StatusBadge`), upload `Modal` with a `Form` (file + title), `Table` (query history view, role-gated).

**Cards**: document list cards. **Tables**: query history table (`compliance_officer`/`admin` only, FR-COMP-004). **Charts**: none. **Buttons**: "Ask", "Upload Document". **Forms**: question input, document upload form. **Modals**: upload document modal.

**Navigation**: Primary nav item "Compliance"; upload action visible only to `compliance_officer`/`admin` (FR-COMP-003).

**Responsive Behavior**: Chat and document panel stack vertically on mobile, with a tab switcher.

**Accessibility**: Chat messages are screen-reader announced as they arrive (`aria-live="polite"`); citation chips are keyboard-focusable links.

**Expected API Calls**: `POST /api/v1/compliance/query`, `GET /api/v1/compliance/documents`, `POST /api/v1/compliance/documents`, `GET /api/v1/compliance/queries`.

**Expected JSON**: see `docs/08_API_SPECIFICATION.md` §9.

**Loading State**: typing-indicator animation in `ChatWindow` while awaiting an answer (target < 8s, NFR-PERF-004).

**Empty State**: "No documents ingested yet" prompt directing `compliance_officer`/`admin` to upload one; chat disabled until at least one document exists.

**Error State**: if the Copilot returns `insufficient_info: true`, render a distinct neutral (non-error) message bubble — this is expected behavior, not a failure (FR-COMP-002); actual API failures show a retry `Toast`.

**Acceptance Criteria**: every non-insufficient answer renders at least one citation chip (FR-COMP-001).

---

## 5. Incident Reports

**Purpose**: Review, approve, and export auto-drafted incident reports (FR-REP-001–004).

**Wireframe Description**: `Table` of incidents (status, zone, date, severity) with a detail `Modal`/side-panel showing the full drafted report, linked evidence (detections, sensor readings, risk score, emergency recommendation), and an approval action bar for permitted roles.

**Components**: `Table`, `StatusBadge` (draft/approved), `Card` (evidence summary), `Timeline` (evidence chronology), approval `Modal`.

**Cards**: evidence summary cards within the detail view. **Tables**: main incident list table. **Charts**: none. **Buttons**: "Approve", "Export PDF", "Export Markdown". **Forms**: none (evidence read-only per FR-REP-003). **Modals**: incident detail/approval modal.

**Navigation**: Primary nav item "Reports"; visible to `safety_manager`, `admin`, `viewer` (read-only for `viewer`).

**Responsive Behavior**: Table becomes a stacked card list on mobile; detail view becomes full-screen.

**Accessibility**: Status changes (draft → approved) announced via `aria-live`; export buttons labeled with format explicitly (not icon-only).

**Expected API Calls**: `GET /api/v1/incidents`, `GET /api/v1/incidents/{id}`, `PATCH /api/v1/incidents/{id}/approve`, `GET /api/v1/incidents/{id}/export`.

**Expected JSON**: see `docs/08_API_SPECIFICATION.md` §11.

**Loading State**: `LoadingSkeleton` table rows.

**Empty State**: "No incidents recorded" (positive framing, consistent with Alert Center empty state).

**Error State**: approval failure (e.g. already approved, 409) shows a `Toast` explaining the conflict and refreshes the row state.

**Acceptance Criteria**: approve action is available only to `safety_manager`/`admin`; export is disabled until `status: approved` (FR-REP-004).

---

## 6. Analytics

**Purpose**: Historical trends across risk, incidents, compliance, and agent performance (FR-ANL-001–005).

**Wireframe Description**: Top filter bar (site/zone, time range). Grid of `Chart` widgets: risk trend line, incident frequency bar chart, compliance posture summary card, agent performance table.

**Components**: `Chart` (Recharts line/bar variant), `Card`, `Table`, filter bar, export `Button` (P3, FR-ANL-005).

**Cards**: compliance posture summary card. **Tables**: agent performance table. **Charts**: risk trend line chart, incident frequency bar chart. **Buttons**: time-range toggle, export (future scope). **Forms**: filter form. **Modals**: none.

**Navigation**: Primary nav item "Analytics"; visible to all roles.

**Responsive Behavior**: Chart grid reflows 2-column → 1-column; charts remain horizontally scrollable rather than clipped on narrow viewports.

**Accessibility**: Every chart has a text-table fallback toggle for screen-reader users; axis labels never rely on color alone.

**Expected API Calls**: `GET /api/v1/analytics/risk-trends`, `GET /api/v1/analytics/incident-frequency`, `GET /api/v1/analytics/compliance-summary`.

**Expected JSON**: see `docs/08_API_SPECIFICATION.md` §7.

**Loading State**: chart-shaped `LoadingSkeleton` placeholders.

**Empty State**: "No data available for the selected range" per-widget (not a blank/broken chart, per UC-07 exception flow).

**Error State**: failed widget shows an inline retry affordance without blocking the rest of the page.

**Acceptance Criteria**: matches FR-ANL-001–004 acceptance criteria.

---

## 7. Settings

**Purpose**: Platform administration — users, sites, zones, cameras, sensors, thresholds (FR-ADM-001–005). Component: `AdminPage.jsx`.

**Wireframe Description**: Tabbed layout: "Users", "Sites & Zones", "Cameras & Sensors", "Thresholds", "Audit Log". Each tab hosts a `Table` with row actions and a "+ Add" `Button` opening a `Modal` `Form`.

**Components**: `Table`, `Modal`, `Form` fields (text/select/toggle), `StatusBadge` (active/inactive), `Card` (threshold sliders per site).

**Cards**: threshold configuration cards per site. **Tables**: users, sites/zones, cameras/sensors, audit log tables. **Charts**: none. **Buttons**: Add/Edit/Deactivate per entity. **Forms**: user creation/edit, site/zone creation, camera/sensor registration, threshold form. **Modals**: create/edit modals per entity type.

**Navigation**: Primary nav item "Settings"; entire page gated to `admin` role only (server-enforced per NFR-SEC-002; UI hides the nav item for other roles).

**Responsive Behavior**: Tabs collapse into a dropdown selector on mobile; tables become stacked cards.

**Accessibility**: All form fields have associated `<label>` elements; destructive actions (deactivate) require a confirmation `Modal`.

**Expected API Calls**: `GET/POST /api/v1/admin/users`, `PATCH /api/v1/admin/users/{id}`, `GET/POST /api/v1/admin/sites`, `GET/POST /api/v1/admin/cameras`, `GET/POST /api/v1/admin/sensors`.

**Expected JSON**: see `docs/08_API_SPECIFICATION.md` §12.

**Loading State**: `LoadingSkeleton` table rows per tab.

**Empty State**: "No users yet — invite your first team member" (and analogous per tab).

**Error State**: validation errors shown inline on the relevant form field (mapped from the API's `422` response); network errors show a `Toast`.

**Acceptance Criteria**: matches FR-ADM-001–005 acceptance criteria; all actions produce an `audit_logs` entry (FR-ADM-005).

---

## 8. Login

**Purpose**: Authenticate a user session (FR-AUTH-001).

**Wireframe Description**: Centered card with SentinelAI logo/wordmark, email + password fields, "Sign in" button, error message region.

**Components**: `Card`, `Form` (email, password), `Button`.

**Cards**: single centered auth card. **Tables**: none. **Charts**: none. **Buttons**: "Sign in". **Forms**: login form. **Modals**: none.

**Navigation**: Unauthenticated landing route; redirects to Dashboard on success.

**Responsive Behavior**: Card is full-width with padding on mobile, fixed max-width (400px) centered on desktop.

**Accessibility**: Form fields labeled and associated with `aria-describedby` error text; submit reachable via Enter key.

**Expected API Calls**: `POST /api/v1/auth/login`.

**Expected JSON**: see `docs/08_API_SPECIFICATION.md` §2.

**Loading State**: "Sign in" button shows a spinner and disables while the request is in flight.

**Empty State**: not applicable.

**Error State**: invalid credentials show an inline message ("Email or password is incorrect") without revealing which field was wrong (per security best practice).

**Acceptance Criteria**: matches FR-AUTH-001 acceptance criteria; rate-limited per `docs/08_API_SPECIFICATION.md` §1 Auth tier.

---

## Glossary

| Term | Definition |
|---|---|
| Role-gated | UI element or page whose visibility/access depends on the authenticated user's role |
| Optimistic UI update | Frontend updates state immediately, before server confirmation, then reverts on failure |

## References

- `docs/08_API_SPECIFICATION.md`, `docs/10_COMPONENT_LIBRARY.md`, `docs/02_SYSTEM_ARCHITECTURE.md` §5, `docs/03_FUNCTIONAL_REQUIREMENTS.md`

## Assumptions

- The "Settings" page title (per this prompt's required page list) maps to the previously-named `AdminPage.jsx` component and Administration module — documented explicitly in the Page ↔ Component Naming table to avoid a naming contradiction with `docs/02_SYSTEM_ARCHITECTURE.md` §5.

## Future Improvements

- Add a dedicated mobile navigation spec once the mobile companion app (Future Scope) is scoped.
- Add dark mode wireframe variants (tracked in `docs/TASK_BOARD.md` Frontend backlog).
