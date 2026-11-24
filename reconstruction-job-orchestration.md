---
updated: 2026-11-24
---

# Plan orchestration strategy

Execution protocol for `reconstruction-job-lifecycle-plan.md` (the plan) on branch `job-lifecycle`. The operator points a fresh session at this file and says go; that session is the orchestrator. The orchestrator never executes a phase itself and never touches workload code — its only commit kind is a prose commit amending the plan or this file. All phase and audit work is done by spawned subagents.

## Style guides

The four style guides are canonical at `/workspace/agent-style-guides/` for the purposes of this orchestration: `code-quality-guidelines.md` (control flow, single-call-site inlining, ordering, typing), `commenting-guidelines.md` (comment placement, density, form, messages), `response-style-guide.md` (agent prose), `rebase-style-guide.md` (landing-time branch shape). Every style reference in this orchestration resolves there. Where AGENTS-SHARED, the plan, or any agent doc conflicts with them, the guides win.

## Role split

- **Orchestrator** (the session running this file): spawns the phase agent and the audit agents for each phase in sequence, measures each session, enforces the sizing rule, amends the plan on sizing failure, reports, and yields at the end or on a stop condition.
- **Phase agent** (subagent, `general`, fresh context): executes exactly one phase as a plan session per the plan's Session mechanics — reads the plan then the ADR sections the phase cites, verifies a clean tree, executes the steps, follows the commit discipline (code/prose/codegen separated, canonical codegen messages), runs the phase's scoped Verification block, flips the status to `done` with date and HEAD SHA, commits the plan update as prose, and returns a summary listing every error and its resolution. Assume it knows nothing from the orchestrating session; the spawn prompt is self-contained.
- **Audit agents** (two per phase, `general`, fresh context each): each audits exactly one phase's diff against exactly one guide and fixes violations. Neither implements nor designs. The code-quality audit runs first and the comments audit runs second, in that fixed order — shape fixes (inlining, reordering, flattening) displace and orphan comments, so comments must be judged on the post-cascade shape.

## Audit scope

The auditable surface is the diff from the phase's reset target to the phase agent's final HEAD, restricted to source files, excluding `packages/generated/`, `stack/generated/`, lock files, and all prose. Only lines the phase agent added or changed are fixable. A violation whose correct fix requires touching lines the phase did not touch is report-only: recorded in the audit yield, surfaced by the orchestrator in the final ledger, never fixed. If the auditable diff is empty (a prose-only phase), skip both audits.

## Per-phase procedure

1. Read the plan's Status table; take the first phase whose status is not `done`. Never run two phases concurrently, never reorder, never re-run a done phase.
2. Record the reset target (`git rev-parse HEAD`) and require a clean tree at `/workspace/placeframe` on `job-lifecycle`. Dirty tree ⇒ stop and report.
3. Spawn one `general` phase agent: repo root and branch, plan path, phase number, instruction to follow the plan's Session mechanics for that one phase, and the error-and-resolution yield requirement.
4. When it returns, extract its session id (`ses_...`) from the task result and measure per the queries below. Apply the sizing rule before any audit runs.
5. Compute the auditable diff per Audit scope. If empty, skip to step 8.
6. Spawn the code-quality audit agent. The spawn prompt carries, self-contained: repo root and branch, the diff range, the scope rule and exclusions, the absolute path to `code-quality-guidelines.md`, the phase's Verification block commands, the commit discipline (fixes are code commits; prose never), and the yield requirement. It fixes, commits, then re-runs the phase's Verification block and requires green.
7. When it returns, spawn the comments audit agent with the same contract against `commenting-guidelines.md`.
8. Measure every audit session like a phase session; apply the sizing rule to each.
9. Report one line: phase, outcome, audits (fixed N / clean / skipped), cumulative tokens across the phase's sessions, peak context (max across them), cost.
10. Repeat until all phases are `done`, then yield with the phase-10 handoff summary, the full per-phase ledger, every out-of-scope audit finding, and every error with its resolution.

## Measurement

Database `~/.local/share/opencode/opencode.db`, one set per session (phase and audit alike):

- Cumulative tokens and cost (work/cost figure):
  `SELECT tokens_input, tokens_output, tokens_reasoning, tokens_cache_read, tokens_cache_write, cost FROM session WHERE id = '<ses>';`
- Peak context (sizing figure — the model's working memory at its worst turn):
  `SELECT MAX(json_extract(data,'$.tokens.input') + json_extract(data,'$.tokens.cache.read')) FROM message WHERE session_id = '<ses>';`
- Compaction check (any role beyond `user`/`assistant` means the session compacted):
  `SELECT DISTINCT json_extract(data,'$.role') FROM message WHERE session_id = '<ses>';`

## Sizing rule

A session is mis-sized if peak context exceeds **200,000 tokens**, or if it shows compaction artifacts (compaction resets peak context and masks the first signal). Rationale: the routing model is `glm-5.2` (1M window, 128K output); 200K is the previous-generation window of the family — a phase that fits there lives inside the proven quality envelope, and beyond it leans on long-context training, which is precisely when a phase is too big for one fresh context. The threshold applies to audit sessions identically: a blown audit means the phase diff was too big, which is the same signal and routes to the same split path. Cumulative tokens carry no threshold; report only. The threshold is not re-deliberated during execution.

## On a sizing failure

1. **Discard.** `git reset --hard <pre-phase SHA> && git clean -fd` at the repo root (plain clean, never `-x` — `boatyard.values.yaml` is gitignored and must survive). This is the operator-approved exception to the no-history-rewrite rule; it applies to this branch only. The pre-phase SHA erases the phase's commits and any audit commits after them.
2. **Amend the plan.** The orchestrator splits the oversized phase into lettered sub-phases (2a, 2b, …), redistributing the steps; each sub-phase gets its own scoped Verification block and status row; downstream phases are not renumbered. Committed as its own prose commit.
3. **Retry.** One fresh subagent per sub-phase, sequential, same mechanics and measurement, audits included.
4. **Recursion and floor.** A sub-phase that still fails sizing is split again. A phase that is one coherent step and cannot meaningfully be split stops and surfaces to the operator.

## Stop conditions — surface to the operator, no retry, no split

- Tree dirty at phase entry.
- The phase agent invokes the plan's ambiguity rule (Session mechanics 6).
- A Verification block the phase agent or an audit agent cannot get green.
- Any subagent, phase or audit, errors out without completing.
- Any phase still cannot fit after splitting.

Out-of-scope audit findings are not a stop condition: record them and surface them in the final yield.

## Reporting

Per phase: `Phase N — done | reset (sized wrong) | stopped (reason)` with audit outcomes (fixed N / clean / skipped), cumulative tokens (phase plus audits), peak context, and cost. Final yield: the phase-10 handoff summary, the per-phase ledger, every out-of-scope audit finding, and every error encountered with its resolution.
