# TASK

Before starting, read the following files completely.

claude-prompts/00_MASTER_CONTEXT.md

docs/PROJECT_MEMORY.md

docs/ARCHITECTURE_RULES.md

docs/CODING_STANDARDS.md

docs/01_PRD.md

docs/02_SYSTEM_ARCHITECTURE.md

docs/03_FUNCTIONAL_REQUIREMENTS.md

docs/04_NON_FUNCTIONAL_REQUIREMENTS.md

docs/05_USER_STORIES_AND_USE_CASES.md

docs/06_SYSTEM_WORKFLOW.md

Treat these as immutable project documentation.

Do not contradict them.

If inconsistencies are discovered, resolve them before generating new documents.

---

# ROLE

You are an enterprise engineering team consisting of:

• Principal Backend Architect

• Principal Frontend Architect

• Principal Database Architect

• Senior API Architect

• AI Platform Architect

• UX Architect

• DevOps Architect

Generate implementation-ready engineering documentation.

---

# OBJECTIVE

Generate the complete Engineering Specification Suite.

Everything produced should allow multiple developers to work in parallel without ambiguity.

---

# OUTPUT DIRECTORY

docs/

Generate ALL of the following files.

---

07_DATABASE_DESIGN.md

Include

Database overview

Database philosophy

Normalization strategy

Entity Relationship Diagram (Mermaid)

Every table

Columns

Primary keys

Foreign keys

Indexes

Relationships

Constraints

Sample records

Migration strategy

Future PostgreSQL migration notes

---

08_API_SPECIFICATION.md

Document every REST endpoint.

For every endpoint include

Purpose

Method

URL

Headers

Authentication

Request body

Response body

Status codes

Validation

Error responses

Example JSON

Rate limiting

Implementation notes

Group APIs by module

Dashboard

Vision

Alerts

Analytics

Risk Engine

Compliance

Emergency

Reports

Authentication

Administration

---

09_FRONTEND_SPECIFICATION.md

This should become the frontend developer's handbook.

For every page include

Purpose

Wireframe description

Components

Cards

Tables

Charts

Buttons

Forms

Modals

Navigation

Responsive behavior

Accessibility considerations

Expected API calls

Expected JSON

Loading state

Empty state

Error state

Acceptance criteria

Cover

Dashboard

Camera Monitoring

Alert Center

Compliance Copilot

Incident Reports

Analytics

Settings

Login

---

10_COMPONENT_LIBRARY.md

Document reusable components.

Include

Button

Card

Table

Chart

Sidebar

Navbar

Modal

Toast

Notification

Camera Tile

Risk Meter

Status Badge

Alert Card

Timeline

Chat Window

Loading Skeleton

Each component should include

Props

States

Variants

Accessibility

Usage examples

---

11_AI_ARCHITECTURE.md

Document

Vision Agent

Sensor Agent

Risk Engine

Compliance Copilot

Emergency Agent

Incident Generator

For every AI module include

Purpose

Input

Output

Dependencies

Model

Prompt templates

Limitations

Failure handling

Future improvements

Sequence diagrams

Flowcharts

---

12_FOLDER_STRUCTURE.md

Generate the final repository structure.

Document every folder.

Document every file.

Describe the purpose of every directory.

Include dependency rules.

---

13_CONFIGURATION.md

Document

Environment variables

API keys

Configuration files

Development setup

Production setup

Secrets management

Logging configuration

Feature flags

---

# REQUIREMENTS

Use Mermaid wherever diagrams improve understanding.

Never use placeholder text.

Everything should be implementation-ready.

Every frontend screen must map to backend APIs.

Every API must map to database entities.

Every AI module must map to backend services.

Every service must have a clear responsibility.

---

# CONSISTENCY AUDIT

Before finishing

Verify

Folder structure

Technology stack

Database tables

API names

Screen names

Component names

AI agent names

JSON structures

Naming conventions

Relationships

Resolve every inconsistency automatically.

---

# FINAL STEP

Generate an implementation traceability matrix.

Map

Business Goal

↓

Feature

↓

Module

↓

API

↓

Database

↓

Frontend Screen

↓

AI Agent

↓

Acceptance Test

Ensure every business requirement is traceable to implementation.