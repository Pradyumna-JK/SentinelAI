# Contributing to SentinelAI

Thank you for contributing to SentinelAI — an AI-Powered Industrial Safety Intelligence Platform. This guide defines the workflow every contributor must follow to keep the repository consistent, safe, and production-quality.

Before contributing, read:

- [`docs/PROJECT_MEMORY.md`](./docs/PROJECT_MEMORY.md) — single source of truth
- [`docs/ARCHITECTURE_RULES.md`](./docs/ARCHITECTURE_RULES.md) — system boundaries and rules
- [`docs/CODING_STANDARDS.md`](./docs/CODING_STANDARDS.md) — naming and formatting conventions

---

## Repository Workflow

1. Check [`docs/TASK_BOARD.md`](./docs/TASK_BOARD.md) for open tasks, or open an issue describing the work.
2. Fork or branch from `main`.
3. Make focused changes — one logical concern per branch/PR.
4. Update relevant documentation (`docs/PROJECT_MEMORY.md`, API docs, etc.) in the same PR as any architectural or contract change.
5. Open a pull request against `main` using the PR template.
6. Address review feedback.
7. Squash-merge once approved and checks pass.

---

## Branch Strategy

Trunk-based development with short-lived feature branches.

| Branch | Purpose |
|---|---|
| `main` | Always deployable. Protected — no direct pushes. |
| `feature/<short-description>` | New functionality (e.g. `feature/vision-agent`) |
| `fix/<short-description>` | Bug fixes (e.g. `fix/alert-latency`) |
| `docs/<short-description>` | Documentation-only changes (e.g. `docs/api-reference`) |
| `chore/<short-description>` | Tooling, dependencies, CI (e.g. `chore/eslint-config`) |

Branches should be short-lived (merged within a day or two during the hackathon window) to avoid drift from `main`.

---

## Pull Requests

Every PR must include:

- A clear title following Conventional Commits format (see `CODING_STANDARDS.md` Section 12)
- A summary of what changed and why
- Links to related issues/tasks
- Confirmation that relevant docs were updated
- Screenshots or a short clip for any frontend/UI change

PRs that change API contracts, database schema, or agent interfaces must reference the corresponding section of `ARCHITECTURE_RULES.md` and update `PROJECT_MEMORY.md` Sections 6/7 accordingly.

---

## Code Review Process

- At least one approving review is required before merge (self-merge only permitted for solo hackathon phases with no other active reviewer).
- Reviewers check for: correctness, adherence to `CODING_STANDARDS.md`, architectural boundary violations (`ARCHITECTURE_RULES.md` Section 12), test coverage, and documentation updates.
- Reviewers should block merges that rename existing APIs, tables, modules, or folders without an explicit, documented decision in `PROJECT_MEMORY.md`.

---

## Commit Rules

- Use Conventional Commits: `type(scope): summary` — see `CODING_STANDARDS.md` Section 12 for types and examples.
- Keep commits atomic — one logical change per commit.
- Never commit secrets, API keys, or `.env` files.
- Never commit directly to `main`.

---

## Issue Templates

Use the templates in [`.github/`](./.github) when opening issues:

- **Bug report** — steps to reproduce, expected vs. actual behavior, environment
- **Feature request** — problem statement, proposed solution, affected modules
- **Documentation** — which doc, what's missing/incorrect

---

## Best Practices

- Follow the architectural boundaries in `ARCHITECTURE_RULES.md` — the frontend never calls agents or the database directly; agents never call each other directly.
- Write tests for new backend and agent logic before opening a PR.
- Keep the AI Dashboard and agent outputs explainable — every decision needs a rationale field, per the Explainability principle.
- Update `docs/TASK_BOARD.md` when moving a task between columns.
- When in doubt about a naming or architectural decision, check `docs/PROJECT_MEMORY.md` first; if it's silent, make a reasonable, documented assumption and add it to Section 11 of that file.
