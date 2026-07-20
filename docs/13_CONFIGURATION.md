# 13_CONFIGURATION.md — Configuration

| Field | Value |
|---|---|
| **Document** | 13_CONFIGURATION.md |
| **Version** | 1.0.0 |
| **Author** | SentinelAI Enterprise Engineering Team (DevOps Architect, Principal Backend Architect) |
| **Purpose** | Define every environment variable, configuration file, and setup procedure for local, demo, and production environments. |
| **Dependencies** | `docs/02_SYSTEM_ARCHITECTURE.md` §10/§11, `docs/12_FOLDER_STRUCTURE.md`, `docs/CODING_STANDARDS.md` §1 |
| **Status** | Draft — Hackathon Phase 2 |

### Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0.0 | 2026-07-19 | Enterprise Engineering Team | Initial configuration reference |

---

## 1. Environment Variables

All variables are `SCREAMING_SNAKE_CASE` (per `docs/PROJECT_MEMORY.md` §5) and loaded exclusively via `backend/core/config.py` (pydantic-settings) or Vite's `import.meta.env` — never read ad hoc (`docs/CODING_STANDARDS.md` §1).

### 1.1 Backend (`backend/.env`)

| Variable | Required | Example (local) | Purpose |
|---|---|---|---|
| `ENVIRONMENT` | Yes | `local` | One of `local`, `demo`, `production` |
| `DATABASE_URL` | Yes | `sqlite:///./sentinelai.db` | SQLite locally; `postgresql://user:pass@host:5432/sentinelai` in production |
| `JWT_SECRET_KEY` | Yes | (generated) | Signing key for access/refresh tokens |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |
| `OPENAI_API_KEY` | Yes | (secret) | Used by Compliance Copilot, Emergency Response Agent rationale, Incident Report Generator |
| `CHROMA_DB_PATH` | Yes | `./chroma_data` | Local ChromaDB persistence path (or connection URL if hosted) |
| `VISION_MODEL_PATH` | Yes | `./models/yolov8_sentinelai.pt` | YOLOv8 weights path for Vision Intelligence Agent |
| `VISION_SAMPLING_INTERVAL_MS` | No | `500` | Frame sampling interval for inference |
| `RISK_FUSION_WEIGHT_VISION` | No | `0.6` | Compound Risk Engine fusion weight |
| `RISK_FUSION_WEIGHT_SENSOR` | No | `0.4` | Compound Risk Engine fusion weight |
| `CORS_ALLOWED_ORIGINS` | Yes | `http://localhost:5173` | Frontend origin(s) allowed to call the API |
| `LOG_LEVEL` | No | `DEBUG` | `DEBUG`\|`INFO`\|`WARNING`\|`ERROR`\|`CRITICAL` |
| `WEBSOCKET_ENABLED` | No | `true` | Toggles real-time push vs. polling fallback |
| `AGENT_INGESTION_API_KEY` | Yes | (secret) | Service-to-service key for agent-internal ingestion endpoints (`docs/08_API_SPECIFICATION.md` §4/§5) |

### 1.2 Frontend (`frontend/.env`)

| Variable | Required | Example (local) | Purpose |
|---|---|---|---|
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000/api/v1` | Backend API base URL |
| `VITE_WEBSOCKET_URL` | Yes | `ws://localhost:8000/ws` | Real-time feed endpoint |
| `VITE_ENVIRONMENT` | No | `local` | Used for environment-specific UI banners (e.g. "Demo Environment") |

## 2. API Keys

| Key | Provider | Used By | Storage |
|---|---|---|---|
| `OPENAI_API_KEY` | OpenAI | Compliance Copilot, Emergency Response Agent, Incident Report Generator | Backend environment only, never sent to frontend |
| `AGENT_INGESTION_API_KEY` | Internal | Vision/Sensor Intelligence Agent → backend ingestion endpoints | Backend environment, rotated per `docs/CONTRIBUTING.md` best practices |

No API key is ever committed to the repository, hardcoded, or logged (per NFR-SEC-003 and `docs/CODING_STANDARDS.md` §1).

## 3. Configuration Files

| File | Purpose |
|---|---|
| `backend/core/config.py` | Pydantic-settings class loading all backend env vars into a typed, validated `Settings` object |
| `backend/.env.example` | Documents every backend variable above with placeholder values, committed to the repo |
| `frontend/.env.example` | Documents every frontend variable above, committed to the repo |
| `frontend/vite.config.js` | Build/dev server config; proxies `/api` to the backend in local dev |
| `frontend/tailwind.config.js` | Design token configuration (colors, spacing) referenced by `docs/10_COMPONENT_LIBRARY.md` |
| `database/schema.sql` | Canonical schema definition (`docs/07_DATABASE_DESIGN.md`) |

`.env` files themselves (containing real secrets) are **git-ignored**; only `.env.example` files are committed.

## 4. Development Setup

1. Clone the repository.
2. Copy `backend/.env.example` → `backend/.env`; fill in `OPENAI_API_KEY`, generate a `JWT_SECRET_KEY`, leave `DATABASE_URL` as the default SQLite path.
3. Copy `frontend/.env.example` → `frontend/.env`; defaults work for local dev against a locally running backend.
4. Backend: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --reload` (per `README.md` → Getting Started).
5. Frontend: `npm install && npm run dev`.
6. Database: schema auto-applied on backend startup for SQLite in `local` environment (migrations run automatically); seed data optionally loaded from `database/seed/demo_seed.sql`.

## 5. Production Setup

1. Provision a PostgreSQL instance; set `DATABASE_URL` accordingly.
2. Set `ENVIRONMENT=production`; this disables auto-reload, enables structured JSON logging, and tightens `CORS_ALLOWED_ORIGINS` to the deployed frontend domain only.
3. Run Alembic migrations explicitly as a CI/CD pipeline step before starting the backend (never on-request in production, per `docs/07_DATABASE_DESIGN.md` §8).
4. Deploy backend container to Render/Railway; deploy frontend build to Vercel (per `docs/PROJECT_MEMORY.md` §3).
5. Configure `OPENAI_API_KEY` and `AGENT_INGESTION_API_KEY` as encrypted secrets in the hosting provider's secret manager — never in a committed `.env` file.
6. Point `VITE_API_BASE_URL`/`VITE_WEBSOCKET_URL` (build-time) at the production backend domain.

## 6. Secrets Management

- **Local**: `.env` files, git-ignored, never shared outside the developer's machine.
- **Demo/Production**: platform-native secret managers (Render/Railway environment variable encryption, Vercel encrypted env vars).
- **Rotation**: `AGENT_INGESTION_API_KEY` and `JWT_SECRET_KEY` should be rotated on any suspected compromise; rotating `JWT_SECRET_KEY` invalidates all existing sessions by design.
- **Principle of least privilege**: the `AGENT_INGESTION_API_KEY` grants access only to agent-internal ingestion endpoints (`docs/08_API_SPECIFICATION.md` §4/§5), never the full API surface.

## 7. Logging Configuration

- Configured centrally in `backend/core/logging.py` (per `docs/CODING_STANDARDS.md` §8, `docs/02_SYSTEM_ARCHITECTURE.md` §12).
- `local`: human-readable console logs at `DEBUG`.
- `demo`/`production`: JSON-structured logs at `INFO` (configurable via `LOG_LEVEL`), each entry including a trace ID for cross-agent request tracing.
- No PII or secrets ever logged (NFR-PRIV-002, NFR-SEC-003).

## 8. Feature Flags

| Flag | Default | Purpose |
|---|---|---|
| `WEBSOCKET_ENABLED` | `true` | Falls back to polling (`docs/02_SYSTEM_ARCHITECTURE.md` §14) if real-time infrastructure is unavailable in a given environment |
| `COMPLIANCE_COPILOT_ENABLED` | `true` | Allows disabling the Compliance Copilot module independently (e.g. if no documents are ingested yet for a new deployment) |
| `EMERGENCY_AUTO_TRIGGER_ENABLED` | `true` | Controls whether Critical alerts automatically invoke the Emergency Response Agent (FR-ALT-004) vs. requiring manual trigger during testing |

Feature flags are read from `backend/core/config.py` alongside environment variables (boolean env vars), not a separate flagging service, for MVP simplicity. A dedicated flagging service is noted in Future Improvements.

---

## Glossary

| Term | Definition |
|---|---|
| TTL | Time To Live — duration before a token/credential expires |
| Git-ignored | Excluded from version control via `.gitignore`, never committed |

## References

- `docs/02_SYSTEM_ARCHITECTURE.md`, `docs/12_FOLDER_STRUCTURE.md`, `docs/CODING_STANDARDS.md`, `docs/08_API_SPECIFICATION.md`

## Assumptions

- Specific default values (token TTLs, fusion weights, sampling intervals) are reasonable engineering defaults for the hackathon MVP, not tuned production values; they should be revisited once real usage data exists (consistent with the assumption noted in `docs/04_NON_FUNCTIONAL_REQUIREMENTS.md`).

## Future Improvements

- Migrate feature flags to a dedicated service (e.g. LaunchDarkly-style) once flag count/complexity grows beyond simple boolean env vars.
- Add automated secret-scanning to CI once `.github/workflows/` is implemented.
