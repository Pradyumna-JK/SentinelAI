# TASK

Read and fully understand the following documents before beginning.

claude-prompts/00_MASTER_CONTEXT.md

docs/PROJECT_MEMORY.md

docs/ARCHITECTURE_RULES.md

docs/CODING_STANDARDS.md

docs/ROADMAP.md

These documents are the source of truth.

Never contradict them.

If inconsistencies exist, resolve them before generating new documentation.

---

# ROLE

You are acting as an Enterprise Architecture Team consisting of:

• Principal Product Manager
• Principal Solutions Architect
• Enterprise Software Architect
• AI Systems Architect
• Technical Product Owner
• Business Analyst

Collaboratively design the SentinelAI platform.

Do not simplify.

Write implementation-ready documentation.

---

# OBJECTIVE

Generate the complete Product & Architecture documentation suite.

Every document should be professional enough that software engineers can begin implementation immediately.

---

# OUTPUT DIRECTORY

docs/

Generate the following files.

---

01_PRD.md

Include

• Executive Summary
• Vision
• Problem Statement
• Business Goals
• Product Goals
• Scope
• Out of Scope
• Stakeholders
• User Personas
• Functional Overview
• MVP Scope
• Future Scope
• Risks
• Success Metrics
• Acceptance Criteria

---

02_SYSTEM_ARCHITECTURE.md

This should be extremely detailed.

Include

System Overview

Architecture Principles

Layered Architecture

Component Responsibilities

Frontend Architecture

Backend Architecture

AI Layer

Database Layer

API Layer

Deployment Layer

Scalability

Security

Logging

Monitoring

Performance

Fault Tolerance

Future Expansion

Include Mermaid diagrams

System Diagram

Component Diagram

Layer Diagram

Deployment Diagram

Communication Diagram

---

03_FUNCTIONAL_REQUIREMENTS.md

Generate every functional requirement.

Organize by module.

Dashboard

Vision

Alerts

Analytics

Risk Engine

Compliance

Emergency Response

Reports

Authentication

Administration

Each requirement should have

ID

Priority

Description

Acceptance Criteria

Dependencies

---

04_NON_FUNCTIONAL_REQUIREMENTS.md

Include

Performance

Availability

Scalability

Reliability

Maintainability

Extensibility

Security

Privacy

Compliance

Accessibility

Portability

Disaster Recovery

Monitoring

Logging

Backup Strategy

---

05_USER_STORIES_AND_USE_CASES.md

Generate

User Personas

Use Cases

User Stories

Happy Path

Alternative Flow

Exception Flow

Actor Diagrams

Priority Matrix

Acceptance Criteria

---

06_SYSTEM_WORKFLOW.md

Generate complete workflows.

Include Mermaid diagrams for

Camera Detection

Risk Analysis

Compliance Query

Emergency Response

Dashboard Update

Incident Creation

Authentication

API Flow

---

# DIAGRAM REQUIREMENTS

Use Mermaid extensively.

Generate

flowcharts

sequence diagrams

state diagrams

component diagrams

ER diagrams where relevant

Never use ASCII diagrams.

---

# QUALITY REQUIREMENTS

Every document should include

Version

Author

Purpose

Dependencies

Revision History

Glossary

References

Assumptions

Future Improvements

---

# CONSISTENCY AUDIT

Before finalizing

Verify

Folder names

Technology names

Architecture

Naming conventions

Terminology

Database naming

Module naming

API naming

User roles

Risk engine naming

Agent naming

Fix every inconsistency automatically.

Then regenerate affected sections.

---

# FINAL OUTPUT

Return every document in separate Markdown files.

Ensure all files are internally consistent.

Do not omit sections because of length.

Continue generating until the entire suite is complete.