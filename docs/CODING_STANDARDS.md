# CODING_STANDARDS.md

Enterprise coding standards for the SentinelAI repository. All contributors — human or AI — must follow these standards. Consistent with [`PROJECT_MEMORY.md`](./PROJECT_MEMORY.md) and [`ARCHITECTURE_RULES.md`](./ARCHITECTURE_RULES.md).

---

## 1. Python Coding Standards (Backend & Agents)

- **Style guide**: PEP 8, enforced via `black` (formatting) and `ruff` (linting).
- **Type hints**: mandatory on all function signatures and Pydantic models.
- **Docstrings**: Google-style docstrings on every public function, class, and module.
- **Imports**: standard library → third-party → local, each group alphabetized and separated by a blank line.
- **Async**: all FastAPI route handlers and agent I/O calls (OpenAI API, ChromaDB, DB) must be `async def`.
- **Configuration**: no hardcoded secrets or config; all environment-dependent values loaded via `backend/core/config.py` using `pydantic-settings`.
- **Error handling**: never use bare `except:`; always catch specific exceptions and re-raise as a defined `SentinelAIException` subclass (see Section 7).

```python
async def compute_risk_score(zone_id: str, vision_signals: list[Detection], sensor_signals: list[SensorReading]) -> RiskScore:
    """Compute a compound risk score for a zone.

    Args:
        zone_id: Identifier of the zone being scored.
        vision_signals: Recent Vision Intelligence Agent detections.
        sensor_signals: Recent Sensor Intelligence Agent readings.

    Returns:
        RiskScore: the computed compound risk score with explanation.
    """
    ...
```

---

## 2. React Coding Standards (Frontend)

- **Style guide**: enforced via ESLint (`eslint-config-airbnb` base) and Prettier.
- **Components**: functional components with Hooks only. No class components.
- **Structure**: one component per file; co-locate styles via Tailwind utility classes (no separate CSS files unless a design token override is required).
- **State management**: local state via `useState`/`useReducer`; cross-page state via React Context (`frontend/src/context/`). No additional state library unless documented here first.
- **Data fetching**: all API calls go through `frontend/src/services/` Axios clients — components never call `axios` directly.
- **Props**: destructure props in the function signature; define a `PropTypes` or JSDoc type for every component.

```jsx
function AlertCard({ alert, onAcknowledge }) {
  return (
    <div className="rounded-lg border border-red-500 p-4">
      <p className="font-semibold">{alert.title}</p>
      <button onClick={() => onAcknowledge(alert.id)}>Acknowledge</button>
    </div>
  );
}

export default AlertCard;
```

---

## 3. Folder Naming Conventions

- All folders: lowercase, `kebab-case` if multi-word (e.g. `claude-prompts/`).
- Top-level folders are frozen per `PROJECT_MEMORY.md` Section 4 — never renamed.
- Frontend subfolders (`components/`, `pages/`, `services/`, `hooks/`) always plural, lowercase.

## 4. Component Naming (Frontend)

- React components: `PascalCase`, matching filename exactly (`AlertCard.jsx` exports `AlertCard`).
- Page-level components suffixed `Page` (`DashboardPage.jsx`, `AnalyticsPage.jsx`).
- Reusable UI primitives suffixed by type where useful (`AlertCard.jsx`, `RiskBadge.jsx`, `MetricChart.jsx`).

## 5. File Naming

| Type | Convention | Example |
|---|---|---|
| Python module | `snake_case.py` | `risk_engine.py` |
| React component | `PascalCase.jsx` | `AlertCard.jsx` |
| React hook | `camelCase.js`, prefixed `use` | `useAlertsFeed.js` |
| Test file (Python) | `test_<module>.py` | `test_risk_engine.py` |
| Test file (React) | `<Component>.test.jsx` | `AlertCard.test.jsx` |
| Markdown docs | `SCREAMING_SNAKE_CASE.md` | `ARCHITECTURE_RULES.md` |

## 6. API Naming & REST Conventions

- Base path: `/api/v1`.
- Resource paths: plural nouns, `kebab-case` (`/api/v1/risk-scores`).
- HTTP verbs map to actions: `GET` (read), `POST` (create), `PUT` (full update), `PATCH` (partial update), `DELETE` (remove). No verbs in URLs.
- Nested resources reflect ownership: `/api/v1/sites/{site_id}/zones`.
- Query params for filtering/pagination: `?page=1&limit=25&status=active`.
- Every endpoint returns a consistent envelope:

```json
{
  "success": true,
  "data": { },
  "error": null
}
```

- Endpoint names, once shipped, are never renamed (see `PROJECT_MEMORY.md` Section 12) — breaking changes require a `/api/v2` path.

## 7. Error Handling

- Backend: all exceptions inherit from a base `SentinelAIException`; FastAPI exception handlers translate these into the standard error envelope with an appropriate HTTP status code.
- Every error response includes a machine-readable `error.code` (e.g. `RISK_ENGINE_TIMEOUT`) and a human-readable `error.message`.
- Frontend: all Axios calls wrapped by a shared interceptor (`frontend/src/services/apiClient.js`) that normalizes errors before they reach components.
- Never swallow errors silently. Log, then surface or propagate.

## 8. Logging

- Backend uses Python's `logging` module configured centrally in `backend/core/logging.py`; JSON-structured logs in production.
- Log levels: `DEBUG` (local dev only), `INFO` (normal operation), `WARNING` (recoverable anomaly), `ERROR` (failed operation), `CRITICAL` (safety-relevant failure — e.g. Vision Agent offline).
- Every agent logs a trace ID per request so a decision (e.g. a risk score) can be traced end-to-end through Vision → Sensor → Risk → Emergency.
- Never log secrets, API keys, or raw PII.

## 9. Commenting Standards

- Comments explain **why**, not **what** — the code should already say what it does.
- TODOs must be tagged with an owner and context: `# TODO(pradyumna): replace placeholder threshold once calibration data exists`.
- No commented-out code left in commits.

## 10. Documentation Standards

- All documentation is Markdown, matching the standards defined in `claude-prompts/00_MASTER_CONTEXT.md`.
- Architecture explanations include Mermaid diagrams.
- API documentation includes: Endpoint, Purpose, Request, Response, Error Codes, Authentication, Validation, Example JSON.
- Database documentation includes: ER Diagram, Relationships, Primary Keys, Foreign Keys, Constraints.
- Frontend documentation includes: Wireframes, Components, API Mapping, User Flow.
- AI documentation includes: Input, Output, Model, Flow, Prompt Templates, Limitations.

## 11. Formatting

- Python: `black` (line length 100), import order enforced by `ruff isort` rules.
- JavaScript/JSX: Prettier (2-space indent, single quotes, trailing commas where valid ES5).
- Markdown: one sentence per line is not required, but headings must follow strict hierarchy (no skipped levels).

## 12. Git Commit Message Conventions

Conventional Commits format:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.

Examples:

```
feat(vision-agent): add PPE violation detection
fix(risk-engine): correct compound score weighting bug
docs(architecture): add agent communication diagram
```

Full branch strategy and PR process: see [`CONTRIBUTING.md`](../CONTRIBUTING.md).
