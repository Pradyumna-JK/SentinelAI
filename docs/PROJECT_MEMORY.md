# PROJECT_MEMORY.md

**This is the single source of truth for the SentinelAI repository.**

This document is updated continuously throughout development. Every engineer and every AI assistant working on this repository must read this file before making changes, and must update it after any change that affects architecture, naming, APIs, database schema, or milestones.

Governing document: [`claude-prompts/00_MASTER_CONTEXT.md`](../claude-prompts/00_MASTER_CONTEXT.md) (immutable — never modify).

---

## 1. Current Project Status

| Field | Value |
|---|---|
| Project Name | SentinelAI |
| Tagline | AI-Powered Industrial Safety Intelligence Platform |
| Phase | Engineering Specification Suite (Phase 2, documentation) |
| Timeline | 3-day hackathon build |
| Status | Active development — Product, Architecture, and Engineering Specification documentation suites generated |
| Document Version | 1.2.0 |
| Last Updated | 2026-07-19 |

---

## 2. Architecture Decisions

- **Agent-mediated architecture**: The frontend never calls AI agents directly. All requests flow through the FastAPI backend, which orchestrates agent calls. See `ARCHITECTURE_RULES.md`.
- **Six core agents**, each with a single responsibility: Vision Intelligence Agent, Sensor Intelligence Agent, Compound Risk Engine, Compliance Copilot, Emergency Response Agent, Incident Report Generator.
- **Compound Risk Engine is the aggregation point**: it is the only module permitted to combine Vision and Sensor outputs into a single risk score. No other module computes risk.
- **RAG for compliance only**: ChromaDB + Sentence Transformers are scoped exclusively to the Compliance Copilot. No other agent queries the vector store directly.
- **Database strategy**: SQLite for MVP/hackathon delivery; PostgreSQL is the target production database. Schema must remain portable between both (see `database/` and `ARCHITECTURE_RULES.md`).
- **API versioning from day one**: all endpoints are namespaced under `/api/v1`.
- **Documentation-first**: no implementation code is written until foundational docs (this file, `ARCHITECTURE_RULES.md`, `CODING_STANDARDS.md`) are complete and internally consistent.

---

## 3. Technology Stack (Authoritative)

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React, Vite, TailwindCSS, React Router, Axios, Recharts | SPA served from `frontend/` |
| Backend | Python, FastAPI | REST API, in `backend/` |
| AI | YOLOv8, OpenCV, LangChain / LangGraph, OpenAI API, Sentence Transformers | Agent implementations in `agents/` |
| Vector Database | ChromaDB | Compliance Copilot only |
| Primary Database | SQLite (MVP) → PostgreSQL (Production) | Schema in `database/` |
| Version Control | Git + GitHub | Trunk-based with feature branches, see `CONTRIBUTING.md` |
| Deployment | Docker (optional), Render / Railway / Vercel | See `ROADMAP.md` Phase 4 |

This table must never diverge from `README.md` → Technology Stack. If a technology decision changes, update both files in the same commit.

---

## 4. Folder Structure (Authoritative)

```
SentinelAI/
├── docs/                # Architecture, standards, roadmap, process documentation
├── frontend/            # React + Vite dashboard application
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/    # Axios API clients
│       └── hooks/
├── backend/             # FastAPI application
│   ├── api/              # Route definitions (/api/v1/*)
│   ├── services/         # Business logic, agent orchestration
│   ├── models/           # ORM / Pydantic models
│   └── core/              # Config, security, startup
├── agents/               # AI agent implementations
│   ├── vision_agent.py
│   ├── sensor_agent.py
│   ├── risk_engine.py
│   ├── compliance_copilot.py
│   ├── emergency_agent.py
│   └── incident_generator.py
├── datasets/              # Training/reference datasets, sample media
├── database/               # Schema definitions, migrations, seed data
├── presentation/            # Pitch deck and demo-day presentation assets
├── demo/                    # Demo scripts, sample data, walkthrough assets
├── claude-prompts/          # Governing prompts (00_MASTER_CONTEXT.md, 01_PROJECT_FOUNDATION.md, ...)
├── .github/                 # Issue templates, PR templates, CI workflows
└── tasks/                    # Task tracking artifacts
```

**Rule**: folder names above are frozen. Do not rename, pluralize, or reorganize without updating this file, `README.md`, and `ARCHITECTURE_RULES.md` in the same change.

---

## 5. Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Python files/functions | `snake_case` | `risk_engine.py`, `compute_risk_score()` |
| Python classes | `PascalCase` | `RiskEngine`, `VisionAgent` |
| React components | `PascalCase` | `DashboardPage.jsx`, `AlertCard.jsx` |
| React hooks/functions/vars | `camelCase` | `useAlertsFeed()`, `riskScore` |
| API routes | `kebab-case`, versioned, plural nouns | `/api/v1/incidents`, `/api/v1/risk-scores` |
| Database tables | `snake_case`, plural | `incidents`, `risk_scores` |
| Database columns | `snake_case` | `created_at`, `risk_level` |
| Environment variables | `SCREAMING_SNAKE_CASE` | `OPENAI_API_KEY` |
| Git branches | `type/short-description` | `feature/vision-agent`, `fix/alert-latency` |

Full detail: `CODING_STANDARDS.md`.

---

## 6. Current APIs

All endpoints are namespaced under `/api/v1`. Full contracts (headers, auth, request/response, status codes, validation, errors, example JSON, rate limits) are documented in [`08_API_SPECIFICATION.md`](./08_API_SPECIFICATION.md) as of v1.2.0 — this table tracks existence and ownership only.

| Endpoint | Owner Module | Status |
|---|---|---|
| `/api/v1/auth` | Backend Core | Planned |
| `/api/v1/vision` | Vision Intelligence Agent | Planned |
| `/api/v1/sensors` | Sensor Intelligence Agent | Planned |
| `/api/v1/risk` | Compound Risk Engine | Planned |
| `/api/v1/compliance` | Compliance Copilot | Planned |
| `/api/v1/emergency` | Emergency Response Agent | Planned |
| `/api/v1/incidents` | Incident Report Generator | Planned |
| `/api/v1/alerts` | Backend Core | Planned |
| `/api/v1/dashboard` | Backend Core | Planned |
| `/api/v1/analytics` | Backend Core | Planned |
| `/api/v1/cctv` | Vision Intelligence Agent | Planned |
| `/api/v1/admin` | Backend Core | Planned |
| `/api/v1/health` | Backend Core | Planned |

**Rule**: API names above are frozen once implementation begins. Never rename an existing endpoint — version it (`/api/v2/...`) instead.

*Added in v1.1.0 (see Revision History below): `/api/v1/admin` and `/api/v1/health`, introduced by `docs/02_SYSTEM_ARCHITECTURE.md` and `docs/03_FUNCTIONAL_REQUIREMENTS.md` during the Product & Architecture Suite pass.*

---

## 7. Current Database Tables (Placeholder)

| Table | Purpose |
|---|---|
| `users` | Platform users (operators, supervisors, admins) |
| `sites` | Industrial sites/facilities monitored by SentinelAI |
| `zones` | Sub-areas within a site (e.g. loading dock, furnace bay) |
| `cameras` | CCTV camera registry, linked to zones |
| `sensors` | Industrial sensor registry (gas, temp, vibration, pressure), linked to zones |
| `detections` | Vision Intelligence Agent output events |
| `sensor_readings` | Sensor Intelligence Agent telemetry log |
| `risk_scores` | Compound Risk Engine output per zone/time |
| `incidents` | Incident Report Generator records |
| `alerts` | Alert Module notifications |
| `compliance_documents` | Source documents ingested by Compliance Copilot |
| `compliance_embeddings` | Vector references into ChromaDB |
| `emergency_protocols` | Emergency Response Agent protocol definitions |
| `emergency_recommendations` | Emergency Response Agent output — matched protocol + rationale per triggering alert |
| `audit_logs` | System-wide audit trail |

*Added in v1.2.0: `emergency_recommendations`, plus `threshold_medium`/`threshold_high`/`threshold_critical` columns on `sites` — introduced by `docs/07_DATABASE_DESIGN.md` during the Engineering Specification Suite pass.*

Full ER diagram and constraints: see [`07_DATABASE_DESIGN.md`](./07_DATABASE_DESIGN.md) — table is no longer a placeholder as of v1.2.0.

---

## 8. Completed Milestones

- [x] Master context defined (`claude-prompts/00_MASTER_CONTEXT.md`)
- [x] Project foundation directive defined (`claude-prompts/01_PROJECT_FOUNDATION.md`)
- [x] Repository foundation documentation generated (README, PROJECT_MEMORY, CODING_STANDARDS, ARCHITECTURE_RULES, ROADMAP, TASK_BOARD, CONTRIBUTING, LICENSE)
- [x] Product & Architecture Suite generated (01_PRD, 02_SYSTEM_ARCHITECTURE, 03_FUNCTIONAL_REQUIREMENTS, 04_NON_FUNCTIONAL_REQUIREMENTS, 05_USER_STORIES_AND_USE_CASES, 06_SYSTEM_WORKFLOW)
- [x] Engineering Specification Suite generated (07_DATABASE_DESIGN, 08_API_SPECIFICATION, 09_FRONTEND_SPECIFICATION, 10_COMPONENT_LIBRARY, 11_AI_ARCHITECTURE, 12_FOLDER_STRUCTURE, 13_CONFIGURATION, 14_TRACEABILITY_MATRIX)

---

## 9. Pending Milestones

- [ ] Backend + frontend scaffolding (actual code)
- [ ] Docker + deployment configuration
- [ ] Automated test suites (unit/integration)
- [ ] CI/CD pipeline (`.github/workflows/`)

---

## 10. Design Principles

1. Modular Architecture
2. Explainable AI
3. Scalable Design
4. Clean Folder Structure
5. REST APIs
6. Production Ready
7. Enterprise Documentation
8. Professional UI/UX
9. Separation of Concerns
10. Maintainability

(Sourced verbatim from `claude-prompts/00_MASTER_CONTEXT.md` — do not alter.)

---

## 11. Important Assumptions

Reasonable engineering assumptions made where the master context and foundation directive were silent, per the "make a reasonable engineering assumption and document it clearly" rule:

- `README.md`, `CONTRIBUTING.md`, and `LICENSE` live at the repository root (standard OSS convention); `PROJECT_MEMORY.md`, `CODING_STANDARDS.md`, `ARCHITECTURE_RULES.md`, `ROADMAP.md`, and `TASK_BOARD.md` live under `docs/`.
- API base path is `/api/v1` (not stated explicitly in master context; chosen for REST + versioning compliance).
- SQLite schema is written to be forward-compatible with PostgreSQL (no SQLite-only types) to satisfy the dual-database requirement.
- Authentication scheme is not yet specified upstream; JWT bearer auth is the assumed default until an explicit decision is documented here.
- The two governing prompt files currently at the folder root (`00_MASTER_CONTEXT.md`, `01_PROJECT_FOUNDATION.md`) conceptually belong under `claude-prompts/` per the repository structure; they are referenced with that path throughout the docs even though the source files have not been moved.

---

## 12. Things That Should NEVER Change

- The project name: **SentinelAI**
- The six core agent names: Vision Intelligence Agent, Sensor Intelligence Agent, Compound Risk Engine, Compliance Copilot, Emergency Response Agent, Incident Report Generator
- The frozen folder structure (Section 4)
- Existing API endpoint names (version instead of renaming)
- Existing database table/column names (migrate instead of renaming)
- The rule that the frontend never calls AI agents directly
- The rule that only the Compound Risk Engine computes compound risk
- The five user role keys: `admin`, `safety_manager`, `site_operator`, `compliance_officer`, `viewer` (Section 14)

---

## 14. User Roles (Authoritative)

Introduced in `docs/01_PRD.md` Section 9 during the Product & Architecture Suite pass; reproduced here as the authoritative role set per this file's role as single source of truth.

| Role Key | Persona | Access Summary |
|---|---|---|
| `admin` | Platform Administrator | Full access — users, sites, zones, cameras, sensors, configuration |
| `safety_manager` | Safety Manager | Risk/alerts/incidents oversight, protocol/threshold configuration, report approval |
| `site_operator` | Site Operator | Live dashboard, CCTV, alert acknowledgment, emergency protocol execution |
| `compliance_officer` | Compliance Officer | Compliance Copilot, compliance document ingestion, audit history |
| `viewer` | Executive/Auditor | Read-only — analytics and compliance reporting |

**Rule**: role keys above are frozen once implementation begins, per the same never-rename policy as API endpoints and database tables (Section 12).

---

## 15. Future Roadmap

See [`ROADMAP.md`](./ROADMAP.md) for the full phased plan. Summary:

- **Phase 1** — Foundation & Documentation (this phase)
- **Phase 2** — Core Backend, Database, and Agent Scaffolding
- **Phase 3** — Frontend, Integration, and End-to-End Agent Wiring
- **Phase 4** — Polish, Demo Prep, Deployment

---

## Revision History

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-07-19 | Initial repository foundation (`01_PROJECT_FOUNDATION.md`) |
| 1.1.0 | 2026-07-19 | Product & Architecture Suite pass (`02_PRODUCT_AND_ARCHITECTURE_SUITE.md`): added `/api/v1/admin` and `/api/v1/health` to Section 6; added Section 14 (User Roles) as the authoritative role set introduced by `docs/01_PRD.md`; updated Section 12 (Never Change) accordingly |
| 1.2.0 | 2026-07-19 | Engineering Specification Suite pass (`03_ENGINEERING_SPECIFICATIONS.md`): added `emergency_recommendations` table and `sites` threshold columns to Section 7 (now sourced from `docs/07_DATABASE_DESIGN.md`, no longer a placeholder); Section 6 now sourced from `docs/08_API_SPECIFICATION.md`, no longer a placeholder; updated Sections 8/9 (Milestones) |
