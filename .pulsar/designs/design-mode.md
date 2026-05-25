---
created: 2026-05-25
updated: 2026-05-25
---

# design mode: question protocol, correctness bias, and how constraints get made

## Context

design mode is the first of seven opencode modes drafted in `.pulsar/modes/`. This document designs its behavior; it is also the first artifact produced by design mode, so the process is the demonstration — research, draft, enumerate open questions, close each by citing guidance or by asking with options + tradeoffs.

Research bounding this design:

- `.pulsar/spec-style-guide.md` already frames SPEC.md as the carrier of constraints a reader cannot derive from the code; separates always-loaded `CLAUDE.md` (rules) from on-demand `SPEC.md` (constraints); and rejects status markers, ADR-style supersession, and historical tombstones — "git log is the audit trail" (lines 54, 79–83). A separate initiative renames SPEC.md → constraints.md.
- External ADR practice (adr.github.io, Microsoft Well-Architected, Fowler) treats decision records as immutable, superseded by a new record with a status flip.

The repo's no-history philosophy was chosen over ADR supersession and extended to design documents: a design doc is present truth, not a decision archive (OQ-B).

## Design

Resolved behavior for `.pulsar/modes/design.md`:

1. **Questions are posed as concrete options + tradeoffs with a recommendation** — never open-ended. This document is the worked example.
2. **The "make it durable" follow-up is posed the same way** — options + tradeoffs for whether to codify and which file.
3. **Correctness over expedience.** Lead with the architecturally correct shape; never silently downgrade. Red-flag phrases: "for now," "minimum viable," "bandaid," "surgical fix."
4. **Delete the problem before designing it.** Hunt for an existing package/library/service before designing new code; building is the last resort.
5. **A design eliminates ambiguity completely** — done only when an implementer could build it with zero remaining design decisions.
6. **Design writes constraints on the fly** (OQ-A): when a decision is stable and standalone, design writes the durable guidance immediately to the one constraints file at the narrowest covering subtree root, and commits those edits in the same prose commit as the design doc. design never edits source. When a constraint cannot be written yet — placement blocked, or owned by another initiative — it is held in the doc's *Uncommitted constraints* section, and the design is not done until that buffer is drained (committed constraints are removed from the doc).
7. **Design docs are present truth** (OQ-B): no status field, no history, no supersede. Done-ness is read from an empty Open questions ledger. A redesign overwrites the doc in place and proactively reconciles (reverts/updates) the constraints the prior design wrote.

## Open questions

All closed.

- **OQ-A — Constraint-write timing.** CLOSED (user). Design writes the constraint on the fly when stable and standalone, committed with the design doc in one prose commit; defer to implement only when the constraint needs not-yet-written code.
- **OQ-A2 — CLAUDE.md vs constraints.md.** CLOSED (user delegated; opinion adopted, pending ratification). One guidance file per subtree root. The two-file split protects the always-loaded budget, which is a concern only at the repo root (loaded for every task). A subtree file is loaded only when working there, so there is no always-loaded pressure and no reason to split "rules" from "constraints" — they are all the subtree's constraints. Root keeps one terse always-loaded file (repo-wide hard rules); each subtree has one constraints file; nothing has both. The length cap keeps subtree files loadable (over-cap → split the subtree). Dependency: a constraint not in context is not followed, and the harness auto-loads by filename — settle whether the subtree file keeps an auto-loaded name or opencode is configured to auto-load `constraints.md` before the rename.
- **OQ-B — Redesigning a locked design.** CLOSED (user). No history/supersede; overwrite in place, expunge the prior design, reconcile its constraints. Extends the repo's no-tombstone philosophy to design docs.
- **OQ-C — Capturing the decision criteria.** CLOSED (user). Codify the decided rules now in CLAUDE.md / the renamed constraints-style-guide.

## Uncommitted constraints

Discovered but not yet written to a constraints file. This design is not done until this section is empty.

- design docs are present truth — no status/history/supersede; redesign overwrites in place and reconciles prior constraints → constraints-style-guide. Deferred: owned by the docs-model / SPEC→constraints rename initiative.
- one guidance file per subtree root; root file terse and always-loaded → constraints-style-guide. Deferred: this is the rename initiative's spine, pending A2 ratification.

(The rule that design questions are posed as options + tradeoffs is encoded directly in `.pulsar/modes/design.md`; it needs no separate constraints-file entry.)

## Handoff

plan mode plans the edits to `.pulsar/modes/design.md` plus the constraint / CLAUDE.md / style-guide changes above; implement applies and reconciles. The one-guidance-file-per-subtree-root model (OQ-A2) is large enough to be its own design — it defines the scope of the SPEC.md → constraints.md rename initiative and should be designed separately before execution.
