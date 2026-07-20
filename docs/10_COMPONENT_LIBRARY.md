# 10_COMPONENT_LIBRARY.md — Component Library

| Field | Value |
|---|---|
| **Document** | 10_COMPONENT_LIBRARY.md |
| **Version** | 1.0.0 |
| **Author** | SentinelAI Enterprise Engineering Team (UX Architect, Principal Frontend Architect) |
| **Purpose** | Specify every reusable frontend component referenced by `docs/09_FRONTEND_SPECIFICATION.md`. |
| **Dependencies** | `docs/09_FRONTEND_SPECIFICATION.md`, `docs/CODING_STANDARDS.md` §2/§4 |
| **Status** | Draft — Hackathon Phase 3 |

### Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0.0 | 2026-07-19 | Enterprise Engineering Team | Initial component library, 16 components |

All components live under `frontend/src/components/`, follow `PascalCase` filenames, and use TailwindCSS utility classes exclusively (per `docs/CODING_STANDARDS.md` §2).

---

## 1. Button

**Props**: `variant` (`primary`|`secondary`|`danger`|`ghost`), `size` (`sm`|`md`|`lg`), `disabled` (bool), `loading` (bool), `onClick`, `children`.
**States**: default, hover, focus, active, disabled, loading (spinner replaces label).
**Variants**: `primary` (filled brand color), `secondary` (outlined), `danger` (destructive actions e.g. deactivate user), `ghost` (low-emphasis, e.g. table row actions).
**Accessibility**: native `<button>` element; `aria-busy="true"` when `loading`; disabled buttons are `aria-disabled` and not focusable-but-inert (never `display:none`, so screen readers announce unavailability).
**Usage**:
```jsx
<Button variant="primary" onClick={handleAcknowledge} loading={isAcknowledging}>Acknowledge</Button>
```

## 2. Card

**Props**: `title`, `children`, `variant` (`default`|`elevated`|`outlined`), `onClick` (optional, makes card interactive).
**States**: default, hover (if interactive), focus-visible (if interactive).
**Variants**: `default` (flat), `elevated` (shadow, used for Dashboard risk cards), `outlined` (used in Settings lists).
**Accessibility**: interactive cards render as `<button>` or `role="button"` with `tabIndex=0`; non-interactive cards are plain `<div>`.
**Usage**:
```jsx
<Card title="Loading Dock A" variant="elevated" onClick={openRiskDetail}>...</Card>
```

## 3. Table

**Props**: `columns` (array of `{key, label, sortable}`), `rows`, `onRowClick`, `loading` (bool), `emptyMessage`.
**States**: default, loading (renders `LoadingSkeleton` rows), empty (renders `emptyMessage`), sorted (per-column indicator).
**Variants**: `compact` (Alert Center dense view), `default` (Incident Reports, Settings).
**Accessibility**: semantic `<table>`/`<thead>`/`<tbody>`; sortable headers are `<button>` elements with `aria-sort`.
**Usage**:
```jsx
<Table columns={incidentColumns} rows={incidents} onRowClick={openIncident} emptyMessage="No incidents recorded" />
```

## 4. Chart

Wraps Recharts; used throughout Dashboard and Analytics (`docs/09_FRONTEND_SPECIFICATION.md` §1/§6) for trend lines, bar charts, and per-zone sparklines.

**Props**: `type` (`line`|`bar`|`sparkline`), `data`, `xKey`, `yKey`, `height`, `ariaLabel`.
**States**: default, loading (skeleton), empty (renders "No data available for the selected range").
**Variants**: `line` (risk trends), `bar` (incident frequency), `sparkline` (per-zone mini chart on Dashboard cards).
**Accessibility**: `role="img"` with `aria-label` summarizing the trend; a hidden `<table>` fallback available via a "View as table" toggle (per NFR-ACC accessibility principle in `docs/09_FRONTEND_SPECIFICATION.md` §6).
**Usage**:
```jsx
<Chart type="line" data={riskTrendPoints} xKey="timestamp" yKey="avg_score" height={240} ariaLabel="7-day average risk score trend" />
```

## 5. Sidebar

**Props**: `filters` (site/zone tree), `selected`, `onSelect`, `collapsed` (bool).
**States**: default, collapsed (icon-only), item-selected, item-hover.
**Variants**: `filter` (Dashboard/Camera Monitoring zone filter), `nav` (not used — primary nav lives in `Navbar`).
**Accessibility**: `<nav>` landmark with `aria-label="Site and zone filter"`; keyboard-navigable tree (arrow keys).
**Usage**:
```jsx
<Sidebar filters={siteZoneTree} selected={selectedZoneId} onSelect={setSelectedZoneId} />
```

## 6. Navbar

**Props**: `user` (current authenticated user object), `unacknowledgedCount`, `onLogout`.
**States**: default, role-gated item hidden (e.g. "Settings" hidden for non-`admin`).
**Variants**: `desktop` (full horizontal bar), `mobile` (hamburger + drawer).
**Accessibility**: `<nav>` landmark; current page indicated via `aria-current="page"`; alert badge count announced via `aria-label` ("3 unacknowledged alerts").
**Usage**:
```jsx
<Navbar user={currentUser} unacknowledgedCount={3} onLogout={handleLogout} />
```

## 7. Modal

**Props**: `isOpen`, `onClose`, `title`, `children`, `size` (`sm`|`md`|`lg`|`fullscreen`).
**States**: closed, open, closing (exit transition).
**Variants**: `default` (centered dialog), `fullscreen` (Camera Monitoring expanded view on mobile).
**Accessibility**: `role="dialog"`, `aria-modal="true"`, focus trapped within modal while open, focus returns to the triggering element on close, `Escape` closes.
**Usage**:
```jsx
<Modal isOpen={showUpload} onClose={closeUpload} title="Upload Compliance Document"><UploadForm /></Modal>
```

## 8. Toast

**Props**: `message`, `variant` (`success`|`error`|`info`|`warning`), `duration` (ms), `onDismiss`.
**States**: entering, visible, dismissing.
**Variants**: `success` (e.g. "Alert acknowledged"), `error` (e.g. API failure), `info`, `warning`.
**Accessibility**: `role="status"` (info/success) or `role="alert"` (error/warning) for correct screen-reader urgency; dismissible via keyboard.
**Usage**:
```jsx
<Toast message="Failed to acknowledge alert" variant="error" onDismiss={clearToast} />
```

## 9. Notification

Persistent, in-app notification (distinct from ephemeral `Toast`) surfaced in the `Navbar` bell menu.

**Props**: `items` (array of `{id, message, read, createdAt, link}`), `onMarkRead`, `onNavigate`.
**States**: unread (bold), read (default weight), empty.
**Variants**: `dropdown` (desktop), `sheet` (mobile).
**Accessibility**: bell icon button has `aria-label="Notifications, N unread"`; list is a `role="menu"` with `role="menuitem"` entries.
**Usage**:
```jsx
<Notification items={notifications} onMarkRead={markRead} onNavigate={goTo} />
```

## 10. Camera Tile

**Props**: `camera` (`{id, name, streamUrl, status}`), `detections` (recent, for overlay), `onExpand`.
**States**: `active` (streaming), `offline`, `buffering`.
**Variants**: `grid` (Camera Monitoring grid), `focused` (expanded single view).
**Accessibility**: `aria-label` combining zone/camera name and status ("Dock A - North, active"); overlay bounding boxes have an equivalent text list available in the expanded view.
**Usage**:
```jsx
<CameraTile camera={camera} detections={recentDetections} onExpand={() => openCamera(camera.id)} />
```

## 11. Risk Meter

**Props**: `score` (0–100), `level` (`Low`|`Medium`|`High`|`Critical`), `zoneName`, `onClick`.
**States**: default, hover/focus (interactive, opens rationale detail).
**Variants**: `card` (Dashboard grid), `inline` (Alert Center expanded view, Incident detail).
**Accessibility**: color paired with text label and an icon per level (never color alone, per NFR-ACC-001); `aria-label` e.g. "Loading Dock A, risk level High, score 72".
**Usage**:
```jsx
<RiskMeter score={72.5} level="High" zoneName="Loading Dock A" onClick={openRationale} />
```

## 12. Status Badge

**Props**: `status` (string, e.g. `Healthy`|`Degraded`|`Offline`|`active`|`inactive`|`draft`|`approved`), `variant` (`agent`|`device`|`incident`|`citation`).
**States**: single static display state per render (no interaction).
**Variants**: `agent` (AI agent health), `device` (camera/sensor status), `incident` (draft/approved), `citation` (Compliance Copilot citation chip).
**Accessibility**: text is always present alongside the color swatch; not conveyed by color/icon alone.
**Usage**:
```jsx
<StatusBadge status="Healthy" variant="agent" />
```

## 13. Alert Card

**Props**: `alert` (`{id, severity, zoneName, riskScoreId, acknowledgedBy, createdAt}`), `onAcknowledge`, `onViewRisk`, `expanded` (bool).
**States**: unacknowledged, acknowledged, expanded (shows rationale), collapsed.
**Variants**: `compact` (Dashboard side panel), `full` (Alert Center).
**Accessibility**: severity announced as text ("Critical alert, Loading Dock A"); acknowledge button reachable via keyboard; new arriving cards announced via the page's `aria-live` region (per `docs/09_FRONTEND_SPECIFICATION.md` §3).
**Usage**:
```jsx
<AlertCard alert={alert} onAcknowledge={ack} onViewRisk={openRisk} />
```

## 14. Timeline

**Props**: `events` (array of `{id, label, timestamp, type}`), `orientation` (`vertical`|`horizontal`).
**States**: default, loading (skeleton entries), empty.
**Variants**: `detection` (Camera Monitoring expanded view), `evidence` (Incident Reports evidence chronology).
**Accessibility**: rendered as an ordered list (`<ol>`); each entry's timestamp uses a `<time datetime="...">` element.
**Usage**:
```jsx
<Timeline events={evidenceEvents} orientation="vertical" />
```

## 15. Chat Window

**Props**: `messages` (array of `{id, role, text, citations}`), `onSend`, `isAnswering` (bool), `disabled` (bool, e.g. no documents ingested).
**States**: empty (no messages), typing (awaiting answer), error (failed to answer).
**Variants**: `default` (Compliance Copilot page).
**Accessibility**: message list is `aria-live="polite"`; input has a visible label ("Ask a compliance question"); citation chips are keyboard-focusable links with descriptive `aria-label`s.
**Usage**:
```jsx
<ChatWindow messages={messages} onSend={sendQuestion} isAnswering={isAnswering} disabled={documents.length === 0} />
```

## 16. Loading Skeleton

**Props**: `shape` (`card`|`row`|`chart`|`text`), `count` (number of repeated placeholders), `height`, `width`.
**States**: single animated (pulse) state.
**Variants**: `card`, `row` (table rows), `chart`, `text` (single-line placeholders).
**Accessibility**: `aria-hidden="true"` (decorative — the loading state itself should be announced once via a parent `aria-busy` region, not per-skeleton element).
**Usage**:
```jsx
<LoadingSkeleton shape="row" count={5} />
```

---

## Glossary

| Term | Definition |
|---|---|
| Variant | A visually/behaviorally distinct configuration of a component sharing the same prop contract |
| Interactive card | A `Card` instance that accepts `onClick` and behaves as a control, not just a container |

## References

- `docs/09_FRONTEND_SPECIFICATION.md`, `docs/CODING_STANDARDS.md`

## Assumptions

- Exact Tailwind class tokens (colors, spacing scale) are deferred to implementation; this document specifies behavior/props/accessibility, not pixel-level styling.

## Future Improvements

- Publish this library as a live Storybook instance once `frontend/` scaffolding exists (tracked in `docs/TASK_BOARD.md` Frontend backlog).
