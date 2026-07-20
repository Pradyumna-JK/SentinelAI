# 04_NON_FUNCTIONAL_REQUIREMENTS.md — Non-Functional Requirements

| Field | Value |
|---|---|
| **Document** | 04_NON_FUNCTIONAL_REQUIREMENTS.md |
| **Version** | 1.0.0 |
| **Author** | SentinelAI Enterprise Architecture Team (Enterprise Software Architect, AI Systems Architect, Technical Product Owner) |
| **Purpose** | Define the quality attributes SentinelAI must meet, independent of specific features. |
| **Dependencies** | `docs/02_SYSTEM_ARCHITECTURE.md`, `docs/03_FUNCTIONAL_REQUIREMENTS.md` |
| **Status** | Draft — Hackathon Phase 1 |

### Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0.0 | 2026-07-19 | Enterprise Architecture Team | Initial non-functional requirements set |

### ID Scheme

`NFR-<CATEGORY>-<NNN>`

---

## 1. Performance

| ID | Requirement |
|---|---|
| NFR-PERF-001 | End-to-end latency from camera frame capture to AI Dashboard alert display shall not exceed 5 seconds in the demo environment (per `docs/01_PRD.md` §14). |
| NFR-PERF-002 | The Compound Risk Engine shall compute a risk score within 3 seconds of receiving the triggering signal. |
| NFR-PERF-003 | REST API p95 response time (excluding AI inference calls) shall not exceed 300ms. |
| NFR-PERF-004 | The Compliance Copilot shall return an answer within 8 seconds for a typical query against the ingested document set. |

## 2. Availability

| ID | Requirement |
|---|---|
| NFR-AVAIL-001 | The backend API shall target 99% uptime during demo/production windows (excludes local development). |
| NFR-AVAIL-002 | Loss of the Vision Intelligence Agent shall not take down the Sensor Intelligence Agent, Compound Risk Engine, or dashboard (per Fault Tolerance, `docs/02_SYSTEM_ARCHITECTURE.md` §15). |

## 3. Scalability

| ID | Requirement |
|---|---|
| NFR-SCALE-001 | The backend shall be stateless so that additional instances can be added horizontally without code changes. |
| NFR-SCALE-002 | The database layer shall support migration from SQLite to PostgreSQL without schema redesign (per `docs/ARCHITECTURE_RULES.md` §7). |
| NFR-SCALE-003 | The Vision Intelligence Agent shall be architecturally separable into an independently scaled service without changing its public interface (per `docs/02_SYSTEM_ARCHITECTURE.md` §16). |

## 4. Reliability

| ID | Requirement |
|---|---|
| NFR-REL-001 | Safety-critical writes (`risk_scores`, `incidents`, `alerts`) shall be transactional — no partial writes committed. |
| NFR-REL-002 | If the Compliance Copilot cannot find a relevant document, it shall return an explicit "insufficient information" response rather than a fabricated answer (per FR-COMP-002). |

## 5. Maintainability

| ID | Requirement |
|---|---|
| NFR-MAINT-001 | All backend and agent code shall follow `docs/CODING_STANDARDS.md` (PEP 8, type hints, Google-style docstrings). |
| NFR-MAINT-002 | Every module shall have a single, clearly documented responsibility per `docs/ARCHITECTURE_RULES.md` §2. |
| NFR-MAINT-003 | No module, API, database table, or folder shall be renamed without updating `docs/PROJECT_MEMORY.md` in the same change. |

## 6. Extensibility

| ID | Requirement |
|---|---|
| NFR-EXT-001 | New AI agents shall be addable under `agents/` without modifying existing agent code, by registering with the backend orchestration layer only. |
| NFR-EXT-002 | New API resources shall be addable under `/api/v1` without breaking existing endpoint contracts. |
| NFR-EXT-003 | Risk severity thresholds shall be configurable per site without a code deployment (per FR-ADM-004). |

## 7. Security

| ID | Requirement |
|---|---|
| NFR-SEC-001 | All endpoints except `/api/v1/auth/login` shall require a valid JWT bearer token (per FR-AUTH-002). |
| NFR-SEC-002 | Role-based access control shall be enforced server-side for all five roles; the frontend's role-based UI is a convenience, not a security boundary. |
| NFR-SEC-003 | No secrets, API keys, or credentials shall be committed to the repository or hardcoded (per `docs/CODING_STANDARDS.md` §1). |
| NFR-SEC-004 | All production/demo traffic shall be served over HTTPS. |
| NFR-SEC-005 | Passwords shall be stored using a salted, industry-standard hash (e.g. bcrypt/argon2) — never in plaintext. |

## 8. Privacy

| ID | Requirement |
|---|---|
| NFR-PRIV-001 | Camera footage and detections containing identifiable individuals shall be retained only as long as operationally necessary (retention policy configurable per site). |
| NFR-PRIV-002 | No personally identifiable information shall appear in logs (per `docs/CODING_STANDARDS.md` §8). |

## 9. Compliance

| ID | Requirement |
|---|---|
| NFR-COMP-001 | The platform shall maintain an immutable audit log (`audit_logs`) of all administrative and safety-critical actions. |
| NFR-COMP-002 | The Compliance Copilot shall always cite its source document for regulatory answers, to support audit defensibility (per FR-COMP-001). |

## 10. Accessibility

| ID | Requirement |
|---|---|
| NFR-ACC-001 | The frontend shall meet WCAG 2.1 AA color contrast standards for all alert-severity indicators. |
| NFR-ACC-002 | All interactive dashboard elements shall be keyboard-navigable. |

## 11. Portability

| ID | Requirement |
|---|---|
| NFR-PORT-001 | The backend shall run identically against SQLite (local/demo) and PostgreSQL (production) with only a connection-string change. |
| NFR-PORT-002 | The frontend build shall be deployable to any static host supporting SPA routing (Vercel primary target, per `docs/PROJECT_MEMORY.md` §3). |

## 12. Disaster Recovery

| ID | Requirement |
|---|---|
| NFR-DR-001 | Production database backups shall be taken on a recurring schedule (daily minimum) once on PostgreSQL. |
| NFR-DR-002 | ChromaDB vector store contents shall be re-derivable from `compliance_documents` source files in case of vector store loss. |

## 13. Monitoring

| ID | Requirement |
|---|---|
| NFR-MON-001 | A `/api/v1/health` endpoint shall report backend, database, and vector store connectivity (per `docs/02_SYSTEM_ARCHITECTURE.md` §13). |
| NFR-MON-002 | Each agent shall expose a last-successful-run heartbeat consumed by the AI Dashboard system status panel (per FR-DASH-003). |

## 14. Logging

| ID | Requirement |
|---|---|
| NFR-LOG-001 | All backend and agent logs shall be structured (JSON) in non-local environments (per `docs/CODING_STANDARDS.md` §8). |
| NFR-LOG-002 | Every request/agent-call shall propagate a trace ID enabling end-to-end tracing of a single safety event. |

## 15. Backup Strategy

| ID | Requirement |
|---|---|
| NFR-BAK-001 | Database backups shall be encrypted at rest. |
| NFR-BAK-002 | Backup restoration shall be tested at least once before the platform handles real production site data. |

---

## Glossary

| Term | Definition |
|---|---|
| NFR | Non-Functional Requirement |
| p95 | 95th percentile response time |
| WCAG | Web Content Accessibility Guidelines |

## References

- `docs/01_PRD.md`, `docs/02_SYSTEM_ARCHITECTURE.md`, `docs/03_FUNCTIONAL_REQUIREMENTS.md`, `docs/ARCHITECTURE_RULES.md`, `docs/CODING_STANDARDS.md`

## Assumptions

- Specific numeric SLAs (e.g. 99% uptime, 300ms p95) are reasonable engineering targets for a hackathon-to-production platform; they are not derived from measured infrastructure and should be revisited once real load data exists.
- Password hashing algorithm (bcrypt/argon2) is assumed as industry-standard; final selection deferred to backend implementation.

## Future Improvements

- Replace assumed SLA targets with measured baselines after Phase 3/4 load testing (`docs/ROADMAP.md`).
- Add a formal disaster recovery runbook once deployed to production infrastructure.
