# 15_USER_MANUAL.md — SentinelAI User Manual

| Field | Value |
|---|---|
| **Document** | 15_USER_MANUAL.md |
| **Version** | 1.0.0 |
| **Purpose** | Practical guide to running SentinelAI locally and using every feature that's actually implemented today. |
| **Audience** | You — and anyone else who needs to run or demo the system. |
| **Status** | Reflects the real, live-tested system as of this writing. Earlier docs (01–14) describe the original hackathon-phase spec; where they disagree with this document, this one is current. |

---

## 1. What SentinelAI is

SentinelAI is an AI-powered Industrial Safety Intelligence platform. Its core thesis, directly from
the problem statement: industrial facilities already have plenty of sensors, permits, maintenance
logs, and CCTV — the fatal gap is that nothing correlates them. A gas sensor can read high and a
hot-work permit can be active in the same zone at the same time, and no system flags the combination
until it's too late.

SentinelAI's **Compound Risk Intelligence Engine** is built specifically to close that gap: a
LangGraph multi-agent pipeline that watches gas/IoT sensors, work permits, maintenance activity, and
shift changeovers simultaneously, and raises a specific, explainable finding the moment two or more of
them coincide dangerously — then an **Emergency Response Orchestrator** takes it from there: matching
a protocol, drafting an incident, and raising an alert, automatically.

Everything else in the platform — multi-tenant facility hierarchy, CCTV/vision detection, the
underlying Risk Intelligence Engine, and a RAG-based Compliance Copilot — exists to feed or support
that core loop.

---

## 2. Architecture at a glance

- **Backend**: FastAPI (Python), clean-architecture layout (`api/` → `services/` → `ai/` / `models/`).
- **Database**: PostgreSQL 16 via SQLAlchemy 2 (async) + Alembic migrations. Every business table is
  **multi-tenant isolated twice over**: an automatic ORM-level filter, and PostgreSQL Row-Level
  Security as a database-enforced backstop — a bug in application code still can't leak another
  tenant's rows.
- **Cache / rate limiting**: Redis.
- **Object storage**: MinIO (S3-compatible) — camera evidence, uploaded compliance PDFs.
- **Vector database**: ChromaDB — the Compliance Copilot's document corpus.
- **AI stack**: LangGraph (multi-agent orchestration), LangChain, Google Gemini (chat + embeddings),
  YOLOv8 / ONNX Runtime (vision inference).
- **Frontend**: React + Vite + Tailwind, talking to the backend over a plain REST API (no envelope, no
  `/api/v1` prefix).
- **Auth**: JWT access/refresh tokens, Argon2 password hashing, RBAC (5 system roles).

Five background agents run continuously inside the API process (visible live on the dashboard):
vision inference, the sensor/IoT simulator, the Compound Risk Intelligence Engine, the Risk
Intelligence Engine's scheduler (which also triggers the Emergency Response Orchestrator), and the
Compliance Copilot's document-ingestion worker.

---

## 3. Running the system

### Prerequisites
- Docker Desktop (with WSL2 backend, if on Windows)
- Node.js 18+ (for the frontend dev server)

### First-time setup

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

Edit the root `.env` and fill in:
- All the `change-me-*` credential placeholders (Postgres, Redis, MinIO, JWT secret — generate with
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`).
- **`GEMINI_API_KEY`** — get one (free tier) at aistudio.google.com/apikey. Without a real key, the
  Compliance Copilot and the Emergency Response Orchestrator's incident drafting both degrade
  gracefully to templated fallback text instead of real generated prose (documented in §9).

### Start the backend stack

```bash
docker compose up -d --build
```

This brings up 5 containers: `api` (port 8000), `postgres`, `redis`, `minio` (console on host port
9091 — 9001 collides with a Windows/Hyper-V reserved range), and `chroma`. Migrations run
automatically on API container startup. Check status with:

```bash
docker compose ps
```

All five should show `healthy` within about 30 seconds.

### Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Opens on **http://localhost:5173**. It talks to the backend at `http://localhost:8000` by default
(`frontend/.env.example` → `frontend/.env` if you need to change it).

### Where things live

| What | URL |
|---|---|
| Frontend (React app) | http://localhost:5173 |
| Backend Swagger UI | http://localhost:8000/docs |
| Backend ReDoc | http://localhost:8000/redoc |
| MinIO console | http://localhost:9091 |

---

## 4. Demo accounts

Two organizations are seeded automatically, specifically so multi-tenant isolation can be demonstrated
against two real tenants rather than asserted in the abstract.

| Organization | Admin email | Password |
|---|---|---|
| SentinelAI Demo (primary) | `admin@sentinelai.demo` | `8SEd-jljEaBFlF1bCLTNOg` |
| Acme Manufacturing (isolation demo) | `admin@acme-manufacturing.demo` | `8SEd-jljEaBFlF1bCLTNOg` |

**The primary demo tenant's facility hierarchy** (this is where the flagship scenario lives):

```
Riverside Manufacturing (Factory)
└── Riverside Plant 1 (Site)
    ├── Production Hall A (Building)
    │   ├── Loading Dock A       — ZONE-01
    │   └── Assembly Line 3      — ZONE-02
    └── Chemical Storage Block (Building)
        └── Chemical Storage     — ZONE-03  ← the flagship scenario zone
```

Log in via the frontend's login page, or directly:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sentinelai.demo","password":"8SEd-jljEaBFlF1bCLTNOg"}'
```

Use the returned `access_token` as `Authorization: Bearer <token>` on any other request.

---

## 5. Roles & permissions

Five system roles, each a fixed bundle of `resource:action` permission codes:

| Role | Can do |
|---|---|
| **Viewer** | Read-only across every module |
| **Operator** | Viewer + acknowledge alerts |
| **Supervisor** | Operator + write access to incidents, compliance, risk ingestion, sensors, permits, maintenance, shifts, and emergency response — the day-to-day safety-operations role |
| **Manager** | Supervisor + read-only oversight of users/roles |
| **Admin** | Everything, including user/role management and facility hierarchy edits (creating factories/sites/buildings/zones/cameras is treated as a rare, high-impact administrative action) |

Both demo admin accounts above are seeded as **Admin**, so they can exercise every endpoint in this
manual.

---

## 6. Feature walkthrough

### 6.1 Dashboard (`GET /dashboard`)
One call, everything you need for a live overview: per-zone risk scores/levels/active-alert-counts,
total sites/zones/cameras/active-alerts, and live health for all five background agents (Healthy /
Degraded / Offline, with a real last-run timestamp — nothing here is faked; an agent that isn't
running honestly reports Offline).

### 6.2 Facility hierarchy (`/factories`, `/sites`, `/buildings`, `/zones`)
Standard CRUD for the physical hierarchy. Every other module hangs off a `zone_id` from here.

### 6.3 CCTV / Vision Intelligence (`/camera`, `/vision/status`)
`GET /camera` lists registered camera streams (real registry, FK'd to a zone). `GET /vision/status`
reports the live YOLOv8/ONNX inference engine's state — which models are loaded, provider (CPU/GPU),
queue depth, throughput. The PPE and fire/smoke model weight files aren't bundled in this environment
(no GPU host), so the engine honestly reports them `unavailable` rather than pretending to detect
with a missing model — only the general COCO model is loaded.

### 6.4 Alerts (`/alerts`)
The **central notification sink** — every subsystem (vision, risk, sensors, permits, the emergency
orchestrator) writes here, tagged by `source`. List, create manually, or acknowledge.

### 6.5 Incidents (`/incidents`)
Draft → Approved → Closed lifecycle. Created manually via the API, or automatically by the Emergency
Response Orchestrator (tagged `category="emergency_auto"`, with a full evidence bundle in `detail`).

### 6.6 Risk Intelligence Engine (`/risk/*`)
The scoring core: time-decay + compound aggregation of hazard events into a 0–100 score, banded into
Low/Medium/High/Critical, with a rolling average, a linear-regression trend/prediction, and a
rule-based recommended action. Recomputes every 30s in the background for any zone with recent
activity. Endpoints: zone detail, history, two heatmaps (temporal — risk by hour of day; spatial —
hazard density within a camera frame), factory/organization aggregation, and manual detection ingest.

### 6.7 Sensors / IoT-SCADA (`/sensors/*`)
No real hardware exists for this demo, so a background simulator writes a fresh reading per registered
sensor every 15 seconds — deliberately not pure noise: it models a **buildup-and-clear narrative**
(a value can spike above baseline and decay back down over several ticks), so watching it live over a
minute or two actually shows something. `is_anomaly` is a plain baseline-range check, computed and
stored at write time.

### 6.8 Work Permits (`/permits/*`)
Hot work, confined space, electrical, working-at-height, or general. Created `active` immediately (no
separate approval workflow in this build). This is the second half of the flagship scenario.

### 6.9 Maintenance (`/maintenance/*`)
Equipment registry + maintenance activity windows (scheduled → in-progress → completed).

### 6.10 Shifts (`/shifts/*`)
Shift templates (recurring daily start/end time) + logged changeover events. Incidents statistically
cluster around shift changeovers (handoff gaps); this is the signal that captures that.

### 6.11 Compound Risk Intelligence Engine (`GET /compound-risk/zones/{zone_id}`)
**The centerpiece.** Runs on-demand (this endpoint) or every 20 seconds in the background. Four
independent agents — gas sensor, permit, maintenance, shift — run in parallel and fan into one
correlation agent applying a rule-based combination matrix:

| Combination | Severity | hazard_class |
|---|---|---|
| Gas anomaly + hot-work/confined-space permit | 95 (Critical) | `compound_gas_permit` |
| Gas anomaly + active maintenance | 75 (High) | `compound_gas_maintenance` |
| Gas anomaly + recent shift changeover | 55 (Medium) | `compound_gas_shift_changeover` |
| Permit + maintenance + shift changeover, no gas anomaly | 50 (Medium) | `compound_concurrent_activity` |
| Gas anomaly alone | 40 (Low) | `gas_anomaly` |
| Nothing coinciding | 0 | — no event written |

Rule-based and deterministic on purpose — a safety-critical correlation shouldn't hallucinate. A
`combined=true` finding (two or more signals) writes a `RiskEvent` that flows straight through the
*existing* Risk Intelligence Engine's math — no parallel scoring system. The GET endpoint is
read-only/explainability; the background scheduler is what actually persists findings.

### 6.12 Compliance Copilot (`/compliance/*`)
A full RAG pipeline: upload PDFs (background ingestion: extract → chunk → embed → store in ChromaDB),
then ask questions grounded only in what's been ingested — it explicitly says so rather than
fabricating an answer when nothing relevant is found. Conversation memory persists per session.
Streams token-by-token (Server-Sent Events).

`POST /compliance/explain-compound-risk` is the direct tie-in to §6.11: give it a `zone_id`, and it
runs the compound risk graph, builds a question from whatever it finds, and asks the *same* RAG
pipeline to explain why that specific combination is dangerous and what regulations apply — reusing
100% of the existing chat infrastructure.

### 6.13 Emergency Response Orchestrator (`/emergency/*`)
Triggered automatically whenever a zone's risk computes as **Critical** (checked every risk-scheduler
tick, i.e. every 30s). For a given `hazard_class`:
1. Matches a configured protocol — exact match first, then a `general` fallback, then an explicit
   "no protocol configured" gap notice. Never fabricates a protocol.
2. Drafts a structured incident summary via the same Gemini chat client the Compliance Copilot uses —
   falls back to a templated summary if the LLM call fails, so a safety-critical incident still gets
   created even when AI drafting is unavailable.
3. Creates the Incident, raises a Critical Alert, and logs a simulated multi-channel dispatch (SMS /
   email / site PA — no real Twilio/SendGrid/Slack integration exists; this is stated plainly, not
   pretended).
4. A 10-minute cooldown (checking for a recent auto-created incident in the same zone) stops one
   ongoing Critical state from spawning a new incident every 30 seconds.

`POST /emergency/trigger` runs the same flow on demand for a specific zone — but only actually fires
if that zone is genuinely Critical right now; it won't fabricate a Critical state to force a demo.
`GET`/`POST /emergency/protocols` manage the protocol library.

---

## 7. Reproducing the flagship demo scenario

The seeded demo data already sets this up in Chemical Storage (ZONE-03): a gas sensor, an active
hot-work permit, in-progress equipment maintenance, and a recent shift changeover — all four signals
at once. To watch it fire from scratch (e.g. after a fresh `docker compose up`):

1. Log in as `admin@sentinelai.demo`.
2. `GET /sensors` — note the Chemical Storage Gas Sensor's `latest_value` and `is_anomaly`.
3. `GET /permits` — note the active `hot_work` permit in Chemical Storage.
4. `GET /compound-risk/zones/{chemical_storage_zone_id}` — if the sensor is currently anomalous, this
   returns `hazard_class: "compound_gas_permit"`, `severity: 95`, `combined: true`, with a plain-English
   rationale.
5. Watch `GET /risk/zones/{zone_id}` over the next minute or two — the score climbs as the background
   scheduler keeps re-detecting the combination and persisting new hazard events.
6. Once it crosses into Critical, check `GET /incidents` — a new incident titled
   `"Critical risk - Chemical Storage"` appears automatically, `category="emergency_auto"`, with the
   matched protocol and evacuation route in its `detail`.
7. `GET /alerts` — a Critical alert with `source="emergency"` appears alongside it.
8. Optionally, `POST /compliance/explain-compound-risk` with that `zone_id` to have the Compliance
   Copilot explain the finding against whatever regulatory documents you've uploaded.

If the gas sensor has already decayed back into its normal range by the time you check (the simulator
clears excursions after a few ticks, same as a real buildup-and-clear event would), `/compound-risk`
will instead report whichever weaker combination is still active — the permit+maintenance+shift-
changeover finding is designed to still be there as a fallback narrative.

---

## 8. Full endpoint reference

Grouped exactly as they appear in the live Swagger UI (`/docs`) — that's always the authoritative,
up-to-date source; this table is a quick-reference snapshot.

| Module | Endpoints |
|---|---|
| **Auth** | `POST /auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/password-reset/request`, `/auth/password-reset/confirm` |
| **Users / Roles** | `GET/POST /users`, `GET/PATCH /users/{id}`, `POST/DELETE /users/{id}/roles/{name}`, `GET /roles` |
| **Facilities** | `GET/POST /factories`, `/sites`, `/buildings`, `/zones` (+ `GET .../{id}`) |
| **Dashboard** | `GET /dashboard` |
| **Camera / Vision** | `GET/POST /camera`, `GET /vision/status` |
| **Alerts** | `GET/POST /alerts`, `POST /alerts/{id}/acknowledge` |
| **Incidents** | `GET/POST /incidents`, `POST /incidents/{id}/approve`, `POST /incidents/{id}/close` |
| **Risk** | `GET /risk`, `/risk/zones/{id}`, `/risk/zones/{id}/history`, `/risk/zones/{id}/heatmap/temporal`, `/risk/zones/{id}/heatmap/spatial`, `/risk/factories/{id}`, `/risk/organization`, `POST /risk/ingest` |
| **Sensors** | `GET/POST /sensors`, `GET /sensors/{id}/readings` |
| **Permits** | `GET/POST /permits`, `POST /permits/{id}/close` |
| **Maintenance** | `GET/POST /maintenance/equipment`, `GET/POST /maintenance/records`, `POST /maintenance/records/{id}/complete` |
| **Shifts** | `GET/POST /shifts`, `GET/POST /shifts/changeovers` |
| **Compound Risk** | `GET /compound-risk/zones/{id}` |
| **Compliance** | `GET/POST /compliance/documents`, `GET/DELETE /compliance/documents/{id}`, `GET/POST /compliance/sessions`, `GET /compliance/sessions/{id}/messages`, `POST /compliance/chat`, `POST /compliance/explain-compound-risk` |
| **Emergency** | `GET/POST /emergency/protocols`, `POST /emergency/trigger` |
| **Health** | `GET /health/live`, `GET /health` |

Every endpoint except `/health*`, `/auth/login`, `/auth/refresh`, and the password-reset pair requires
a bearer access token and the corresponding `resource:action` permission (see §5).

---

## 9. Troubleshooting

**Docker Desktop won't start / "listening on unix://...engine.sock" errors (Windows)**
A stale socket file left over from a previous run. Stop all Docker processes, rename (don't just
delete — Windows sometimes refuses a direct delete on these) the offending folder under
`%LOCALAPPDATA%\docker-secrets-engine` or `%LOCALAPPDATA%\Docker\run`, run `wsl --shutdown`, then
relaunch Docker Desktop.

**Compliance Copilot answers are all templated / "insufficient information" / incident summaries look
templated instead of AI-generated**
`GEMINI_API_KEY` is a placeholder. Every Gemini-dependent path (embeddings, chat, incident drafting)
is built to fail gracefully rather than break the feature — but you need a real key for actual
generated content. Update `GEMINI_API_KEY` in the root `.env` and `SENTINEL_GEMINI_API_KEY` in
`backend/.env`, then `docker compose up -d --build api`.

**A container won't go healthy**
`docker compose logs <service> --tail 50` — the API's structured JSON logs name the exact dependency
or migration step that failed.

**Alembic / migration tooling from the host** (only relevant if you're modifying the schema)
The `api` container talks to Postgres on the internal Docker network at port 5432; running Alembic
from the host needs a temporary `ports: ["5433:5432"]` mapping on the `postgres` service in
`docker-compose.yml` plus `SENTINEL_POSTGRES_PORT=5433` in `backend/.env` — remove both again once
you're done.

---

## 10. Extending the system

Every module in this build follows the same pattern, so adding another one is mechanical:

1. A lean SQLAlchemy model, `TenantScoped` (`app/models/`), registered in `app/models/__init__.py`.
2. `alembic revision --autogenerate`, then a hand-written RLS-extension migration
   (`ALTER TABLE ... ENABLE/FORCE ROW LEVEL SECURITY` + a `tenant_isolation` policy) — copy an existing
   one and change the table name.
3. A permission-seed migration if new `resource:read`/`resource:write` codes are needed
   (`app/core/permissions.py` is the single source of truth).
4. A thin service (`app/services/`) and router (`app/api/`), wired into `app/main.py`.
5. Verify: `alembic upgrade head` → `alembic downgrade -N` → `alembic upgrade head` → `alembic check`
   (no drift), then `docker compose up -d --build`, then live HTTP calls against both demo tenants to
   confirm isolation holds.
