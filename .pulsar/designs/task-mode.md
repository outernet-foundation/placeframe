---
created: 2026-05-25
updated: 2026-05-25
---

# task mode: the single durable backlog

## Context

task mode is one of the opencode modes alongside design, plan, implement, diagnose, audit, research, rebase, and commit. Each of the others owns a verb — design produces a design doc, plan a plan, implement code changes, commit and rebase shape history — but none owns the running backlog of what to do next. That cross-cutting action needs its own mode, however small.

The in-session harness task tools are ephemeral; nothing of the backlog survives a session without being written to the repo. task mode closes that gap with a durable repo file, and is portable to opencode, where no such harness tools exist and the file simply is the list.

placeframe does not use the Pulsar epic/ticket system (that lives in `/workspace` and feeds the board), so a single flat file collides with nothing here.

## Design

- **One file: `.pulsar/tasks.md`.** A single backlog for the whole repo. No second list, no per-area list.
- **Present truth.** The list holds only open tasks. A finished task is removed — not struck through, not moved to a Done section. Git log is the audit trail. Same discipline as the spec-style-guide (no status markers, no tombstones) and present-truth design docs.
- **Grouped by initiative.** Lightweight `## <initiative>` headers, flat within each; order within a group is priority.
- **Append anywhere, groom in task mode.** Any mode may add a task the moment it surfaces, so a fleeting follow-up is never lost to a mode switch; task mode owns grooming — reorder, split, refine, remove-on-done.
- **task mode's whole job** is editing that file. It adds nothing else to the repo.

## Open questions

All closed.

- Done-task handling. CLOSED (autonomous, via the spec-style-guide present-truth / no-tombstone philosophy): completed tasks are removed; git log is the record.
- Mutation policy. CLOSED (user): append anywhere, groom in task mode.
- Structure. CLOSED (user): lightweight initiative groups, flat within.
- Board visibility. CLOSED (user): standalone list, not on the Pulsar board — the accepted trade for simple and portable.

## Uncommitted constraints

None. The present-truth, one-file, append-and-groom rules are task-mode behavior and live in `.pulsar/modes/task.md`; no separate constraints-file entry is warranted.

## Handoff

No plan/implement needed — task mode is defined directly in `.pulsar/modes/task.md`. commit mode, which pairs with rebase, still needs its own design.
