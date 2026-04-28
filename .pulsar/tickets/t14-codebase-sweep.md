---
id: T14
title: Codebase sweep — harvest TODOs into tickets
status: plan-needed
depends_on: [T21]
---

# T14: Codebase sweep — harvest TODOs into tickets

## Goal

One-time sweep of the entire codebase to find inline work items (TODOs, FIXMEs, bug references, "future work" language), triage them into roadmap tickets, and enable Ruff `FIX002` to prevent bare TODOs going forward.

## Context

The codebase has accumulated TODO/FIXME comments, GitHub issue references, and "future work" / "not yet implemented" language across Python, C#, and markdown files. These represent untracked work. After harvesting them into proper tickets, a lint rule prevents new bare TODOs from landing.

## Approach

1. **Grep the codebase** for:
   - `TODO`, `FIXME`, `HACK`, `XXX` comments
   - GitHub issue/PR URLs
   - "future work", "not yet implemented", "will be added", "placeholder" language
2. **Read surrounding context** for each hit to understand the actual work item.
3. **Deduplicate against existing roadmap** — some may already be covered by T1-T15.
4. **Present candidates to user** for triage — which become tickets, which get deleted, which are already covered.
5. **Create ticket stubs** for approved items (detail file + roadmap entry, status "Design needed" or "Plan needed").
6. **Clean up the code** — remove bare TODOs for items that became tickets, or replace with ticket references (e.g., `TODO(T16)`) where context is useful to keep inline.
7. **Enable Ruff `FIX002`** (`line-contains-todo`) in `pyproject.toml` so future bare TODOs fail linting. TODOs with ticket references (e.g., `TODO(T16)`) can be allowed via a `noqa` or by scoping the rule.

## Key files

- `pyproject.toml` — Ruff config (add `FIX002`)
- `.pulsar/tickets/roadmap.md` — add new tickets
- `.pulsar/tickets/` — new ticket detail files

## Done when

- All TODO/FIXME/HACK/XXX comments have been triaged (turned into tickets, removed, or annotated with ticket references)
- No GitHub issue URLs remain as bare inline references without corresponding tickets
- Ruff `FIX002` is enabled and `ruff check .` passes
- New tickets appear in `roadmap.md` with detail files
