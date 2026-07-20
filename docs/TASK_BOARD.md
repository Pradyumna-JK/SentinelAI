# TASK_BOARD.md

Kanban-style task board for SentinelAI, organized by discipline. Move tasks left→right as work progresses: **Backlog → To Do → In Progress → Testing → Completed**. Aligned with `ROADMAP.md` phases.

---

## Frontend

| Backlog | To Do | In Progress | Testing | Completed |
|---|---|---|---|---|
| Mobile-responsive layout pass | Scaffold React + Vite + Tailwind app | — | — | — |
| Dark mode support | Build `DashboardPage.jsx` | | | |
| Multi-site selector | Build `CctvPage.jsx` | | | |
| | Build `AlertsPage.jsx` | | | |
| | Build `AnalyticsPage.jsx` (Recharts) | | | |
| | Set up `services/apiClient.js` (Axios) | | | |
| | Set up React Router routes | | | |

## Backend

| Backlog | To Do | In Progress | Testing | Completed |
|---|---|---|---|---|
| Rate limiting | Scaffold FastAPI app (`backend/main.py`) | — | — | — |
| API key rotation | Implement `/api/v1/auth` | | | |
| Multi-tenant org support | Implement `/api/v1/dashboard` | | | |
| | Implement `/api/v1/alerts` | | | |
| | Implement `/api/v1/analytics` | | | |
| | Set up standard response envelope + error handling | | | |
| | Set up centralized logging (`backend/core/logging.py`) | | | |

## AI (Agents)

| Backlog | To Do | In Progress | Testing | Completed |
|---|---|---|---|---|
| Predictive risk modeling | Vision Intelligence Agent — YOLOv8 detection pipeline | — | — | — |
| Multi-language Compliance Copilot | Sensor Intelligence Agent — telemetry parsing | | | |
| Edge deployment of Vision Agent | Compound Risk Engine — fusion logic | | | |
| | Compliance Copilot — ChromaDB ingestion + RAG | | | |
| | Emergency Response Agent — protocol matching | | | |
| | Incident Report Generator — structured report drafting | | | |
| | Define prompt templates for each LLM-backed agent | | | |

## Database

| Backlog | To Do | In Progress | Testing | Completed |
|---|---|---|---|---|
| PostgreSQL production migration | Design ER diagram (`docs/DATABASE_SCHEMA.md`) | — | — | — |
| Read replicas | Implement SQLite schema (MVP) | | | |
| | Write ORM models (`backend/models/`) | | | |
| | Seed data for demo (`database/seed/`) | | | |

## Deployment

| Backlog | To Do | In Progress | Testing | Completed |
|---|---|---|---|---|
| CI/CD pipeline (`.github/workflows/`) | Dockerfile for backend | — | — | — |
| Autoscaling config | Dockerfile for frontend | | | |
| | Deploy to Render/Railway (backend) | | | |
| | Deploy to Vercel (frontend) | | | |

## Presentation

| Backlog | To Do | In Progress | Testing | Completed |
|---|---|---|---|---|
| Post-hackathon investor deck | Build pitch deck outline (`presentation/`) | — | — | — |
| | Record demo walkthrough (`demo/`) | | | |
| | Prepare live-demo fallback (recorded video) | | | |

## Documentation

| Backlog | To Do | In Progress | Testing | Completed |
|---|---|---|---|---|
| Post-hackathon public docs site | OpenAPI/Swagger auto-generation (supersedes hand-authored `08_API_SPECIFICATION.md` once implemented) | — | — | Repository foundation docs (README, PROJECT_MEMORY, CODING_STANDARDS, ARCHITECTURE_RULES, ROADMAP, TASK_BOARD, CONTRIBUTING, LICENSE) |
| | Storybook instance (supersedes `10_COMPONENT_LIBRARY.md` once implemented) | | | Product & Architecture Suite (`01_PRD`, `02_SYSTEM_ARCHITECTURE`, `03_FUNCTIONAL_REQUIREMENTS`, `04_NON_FUNCTIONAL_REQUIREMENTS`, `05_USER_STORIES_AND_USE_CASES`, `06_SYSTEM_WORKFLOW`) |
| | | | | Engineering Specification Suite (`07_DATABASE_DESIGN`, `08_API_SPECIFICATION`, `09_FRONTEND_SPECIFICATION`, `10_COMPONENT_LIBRARY`, `11_AI_ARCHITECTURE`, `12_FOLDER_STRUCTURE`, `13_CONFIGURATION`, `14_TRACEABILITY_MATRIX`) |

---

**Board maintenance rule**: whenever a task moves columns, update this file in the same commit as the corresponding code change. Do not let the board drift from actual repository state.
