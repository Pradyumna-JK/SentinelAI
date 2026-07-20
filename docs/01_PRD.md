# 01_PRD.md — Product Requirements Document

| Field | Value |
|---|---|
| **Document** | 01_PRD.md |
| **Version** | 1.0.0 |
| **Author** | SentinelAI Enterprise Architecture Team (Principal Product Manager, Principal Solutions Architect, Enterprise Software Architect, AI Systems Architect, Technical Product Owner, Business Analyst) |
| **Purpose** | Define the product requirements for SentinelAI — the source of truth for what is being built and why. |
| **Dependencies** | `claude-prompts/00_MASTER_CONTEXT.md`, `docs/PROJECT_MEMORY.md`, `docs/ARCHITECTURE_RULES.md`, `docs/CODING_STANDARDS.md`, `docs/ROADMAP.md` |
| **Status** | Draft — Hackathon Phase 1 |

### Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0.0 | 2026-07-19 | Enterprise Architecture Team | Initial PRD generated from master context and project foundation |

---

## 1. Executive Summary

SentinelAI is an AI-powered Industrial Safety Intelligence Platform that unifies computer vision, sensor telemetry, compound risk analysis, regulatory compliance assistance, and emergency response coordination into a single enterprise dashboard. It is designed to give industrial sites a continuous, explainable, AI-driven safety layer that reduces the time between hazard occurrence and human intervention.

This document defines what SentinelAI must do, for whom, and why — establishing the product baseline that `docs/02_SYSTEM_ARCHITECTURE.md`, `docs/03_FUNCTIONAL_REQUIREMENTS.md`, and the rest of the documentation suite implement against.

## 2. Vision

Every industrial site — regardless of size or budget — should have an always-on AI safety officer watching every camera and every sensor, capable of reasoning about compound risk in real time, keeping operators compliant with evolving regulations, and coordinating the correct emergency response the instant a hazard crosses a critical threshold, while remaining fully explainable to the humans accountable for site safety.

## 3. Problem Statement

Industrial safety monitoring today is fragmented and reactive:

- CCTV footage is monitored by humans who cannot watch every feed continuously, leading to delayed hazard detection (PPE violations, restricted-zone intrusions, fire/smoke, unsafe machine operation).
- Sensor telemetry (gas, temperature, vibration, pressure) is siloed in separate systems, disconnected from visual context.
- Risk is assessed manually and inconsistently, with no unified, explainable score combining visual and sensor evidence.
- Compliance knowledge lives in static PDFs and institutional memory, making it slow to answer "are we compliant with X regulation right now?"
- Emergency response protocols are often paper-based or tribal knowledge, slowing reaction time during a live incident.
- Incident reports are written manually after the fact, often with incomplete evidence trails.

SentinelAI addresses this fragmentation with one integrated, AI-driven platform.

## 4. Business Goals

- Reduce time-to-detection for industrial safety hazards.
- Reduce time-to-response for emergency events.
- Improve regulatory compliance posture and audit readiness.
- Reduce incident investigation and reporting time.
- Provide a defensible, explainable AI safety record for insurance, regulatory, and legal purposes.
- Demonstrate a production-credible platform within the 3-day hackathon timeline (`docs/ROADMAP.md`).

## 5. Product Goals

- Detect safety hazards from live CCTV using the Vision Intelligence Agent with high precision and low false-alarm rate.
- Continuously interpret sensor telemetry via the Sensor Intelligence Agent.
- Fuse vision and sensor signals into one explainable score via the Compound Risk Engine.
- Provide instant, cited answers to compliance questions via the Compliance Copilot.
- Recommend and help coordinate the correct emergency protocol via the Emergency Response Agent the moment risk crosses a critical threshold.
- Auto-draft structured, audit-ready incident reports via the Incident Report Generator.
- Present all of the above through one unified, professional AI Dashboard.

## 6. Scope

**In scope for the platform:**

- Vision Intelligence Agent (YOLOv8 + OpenCV based hazard/PPE/intrusion detection)
- Sensor Intelligence Agent (telemetry ingestion and anomaly detection)
- Compound Risk Engine (vision + sensor fusion into a single explainable score)
- Compliance Copilot (RAG over ingested regulations/SOPs via ChromaDB)
- Emergency Response Agent (protocol recommendation on critical risk)
- Incident Report Generator (auto-drafted structured reports)
- AI Dashboard, Analytics, Alerts, CCTV Monitoring modules
- Authentication and role-based access (Section 9)
- REST API (`/api/v1`) backing all frontend functionality

**In scope for the 3-day hackathon MVP specifically:** see Section 11.

## 7. Out of Scope

- Native mobile applications (web-responsive dashboard only for MVP; mobile app is future scope)
- Direct integration with third-party industrial PLC/SCADA control systems (monitoring only, no control actions)
- Multi-tenant billing/subscription management
- Edge/offline deployment of the Vision Intelligence Agent
- Automated legal liability determination — the Compliance Copilot informs, it does not issue legal rulings
- Autonomous emergency actuation (e.g. automatically shutting down machinery) — the Emergency Response Agent recommends; humans act

## 8. Stakeholders

| Stakeholder | Interest |
|---|---|
| Site Safety Manager | Real-time risk visibility, compliance posture, incident history |
| Site Operator | Actionable alerts, clear dashboard, low false-positive rate |
| Compliance Officer | Accurate, cited regulatory answers, audit trail |
| Platform Administrator | User/site management, system configuration, uptime |
| Executive / Auditor | Historical analytics, compliance evidence, ROI justification |
| Engineering Team | Clear, implementation-ready documentation and stable architecture |
| Hackathon Judges | A credible, working, explainable end-to-end demo |

## 9. User Personas

| Persona | Role Key | Summary |
|---|---|---|
| **Alex — Platform Administrator** | `admin` | Manages users, sites, cameras/sensors, and system configuration. Full access. |
| **Priya — Safety Manager** | `safety_manager` | Owns site safety outcomes. Monitors the AI Dashboard, configures alert thresholds, reviews incidents. |
| **Marcus — Site Operator** | `site_operator` | Works the floor. Watches live CCTV/alerts, acknowledges alerts, escalates emergencies. |
| **Dana — Compliance Officer** | `compliance_officer` | Manages ingested regulatory documents, uses the Compliance Copilot, prepares audit evidence. |
| **Jordan — Executive/Auditor** | `viewer` | Read-only access to Analytics and compliance reports for oversight and audit. |

These five roles are the authoritative user role set for SentinelAI and are referenced identically in `docs/03_FUNCTIONAL_REQUIREMENTS.md`, `docs/04_NON_FUNCTIONAL_REQUIREMENTS.md`, and `docs/05_USER_STORIES_AND_USE_CASES.md`.

## 10. Functional Overview

| Module | Summary |
|---|---|
| AI Dashboard | Unified live view of risk state, alerts, and site status |
| CCTV Monitoring | Live/recorded feeds with in-frame AI annotations from the Vision Intelligence Agent |
| Alerts | Real-time, severity-ranked notifications routed to the correct role |
| Analytics | Historical trends, incident frequency, compliance posture, agent performance |
| Risk Engine | Compound Risk Engine outputs — explainable per-zone risk scores |
| Compliance | Compliance Copilot — RAG-based Q&A over ingested regulations/SOPs |
| Emergency Response | Emergency Response Agent recommendations and protocol tracking |
| Reports | Incident Report Generator output — structured, exportable incident records |
| Authentication | Login, session management, role-based access control |
| Administration | User, site, camera, and sensor management |

Full requirement-level detail: `docs/03_FUNCTIONAL_REQUIREMENTS.md`.

## 11. MVP Scope (3-Day Hackathon)

Per `docs/ROADMAP.md`, the MVP demonstrates one complete, live, end-to-end path:

1. Vision Intelligence Agent detects a hazard from sample/live camera footage.
2. Sensor Intelligence Agent reports a correlated anomaly.
3. Compound Risk Engine fuses both into a single explainable risk score.
4. AI Dashboard displays the elevated risk and a real-time alert.
5. Emergency Response Agent recommends a protocol once risk crosses the critical threshold.
6. Incident Report Generator drafts a structured report from the event.
7. Compliance Copilot answers at least one regulatory question via RAG over a curated document set.

Authentication with the five defined roles is included in MVP scope; full administration UI may be reduced to essential CRUD only.

## 12. Future Scope

- Multi-tenant support for multiple organizations/sites
- Edge deployment of the Vision Intelligence Agent for low-latency on-site inference
- Mobile companion app for field supervisors (`site_operator`, `safety_manager`)
- Third-party IoT sensor network and industrial PLC integration
- Predictive risk modeling from historical incident data
- Multi-language Compliance Copilot for international regulatory frameworks

(Consistent with `README.md` → Future Scope.)

## 13. Risks

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| YOLOv8 model accuracy on limited training/sample data | High | Medium | Use pretrained weights; fine-tune only if time allows; curate a clean demo dataset |
| Integration complexity across 6 agents within 3 days | High | Medium | Strict module boundaries (`docs/ARCHITECTURE_RULES.md`); stub interfaces early, wire incrementally |
| RAG answer quality with a small ingested document set | Medium | Medium | Curate a small, high-quality compliance document set; always cite sources |
| Real-time performance (camera → risk → alert latency) | Medium | Medium | WebSocket/SSE push with polling fallback; async backend throughout |
| Scope creep beyond the single end-to-end demo path | High | High | MVP scope frozen in Section 11; extra features tracked in `docs/TASK_BOARD.md` backlog only |

## 14. Success Metrics

| Metric | Target |
|---|---|
| End-to-end detection-to-alert latency | < 5 seconds (demo environment) |
| Vision Intelligence Agent precision on demo dataset | ≥ 90% |
| Compliance Copilot answer includes a valid citation | 100% of answers |
| Emergency Response Agent triggers on critical risk | 100% of critical-threshold events in demo path |
| Incident Report Generator produces a complete structured report | 100% of triggered incidents |
| Live demo runs without manual intervention | Yes/No (binary gate for Phase 4 exit) |

## 15. Acceptance Criteria

The PRD is considered satisfied when:

- [ ] All modules in Section 10 have corresponding functional requirements in `docs/03_FUNCTIONAL_REQUIREMENTS.md`
- [ ] The MVP end-to-end path (Section 11) runs live against real backend data, not mocked UI
- [ ] All five user roles (Section 9) can authenticate and see role-appropriate views
- [ ] Every AI-driven output (risk score, emergency recommendation, incident report, compliance answer) includes an explanation/rationale, per the Explainability principle in `docs/ARCHITECTURE_RULES.md`
- [ ] Success metrics in Section 14 are measured and reported at Phase 4 (`docs/ROADMAP.md`)

---

## Glossary

| Term | Definition |
|---|---|
| Compound Risk | A unified risk score produced by fusing Vision and Sensor signals for a given zone/time |
| RAG | Retrieval-Augmented Generation — LLM answers grounded in retrieved source documents |
| Zone | A defined sub-area within a site (e.g. loading dock, furnace bay) |
| MVP | Minimum Viable Product — the Section 11 scope for the 3-day hackathon |

## References

- `claude-prompts/00_MASTER_CONTEXT.md` — governing project context
- `claude-prompts/01_PROJECT_FOUNDATION.md` — foundation directive
- `docs/PROJECT_MEMORY.md` — single source of truth
- `docs/ARCHITECTURE_RULES.md` — system boundaries and rules
- `docs/ROADMAP.md` — phased delivery plan

## Assumptions

- The five user roles defined in Section 9 were not specified upstream; they are introduced here as the authoritative role set and must be reflected consistently in all downstream documents.
- "MVP Scope" is interpreted as the Phase 1–3 deliverable per `docs/ROADMAP.md`; "Future Scope" covers everything beyond the 3-day hackathon window.

## Future Improvements

- Add quantitative user research (interviews/surveys) once real site operators are available.
- Expand success metrics with statistically validated precision/recall once a larger labeled dataset exists.
