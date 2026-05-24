# Placeframe SPEC.md Style Guide

A SPEC.md carries the **constraints** that a reader — human engineer or LLM agent — cannot derive from reading the code. Constraints come from two places: authored upfront ("we picked X because Y"), and discovered through iteration ("the non-obvious behavior X exists because Y"). Everything else in a SPEC is in service of presenting those constraints clearly.

This guide is opinionated. Where the field disagrees, this repo picks one.

## The three-file model

| File         | Audience          | Loaded         | Tone                            | Length budget          |
|--------------|-------------------|----------------|---------------------------------|------------------------|
| `CLAUDE.md`  | AI agent          | Every turn     | Imperative rules, commands      | < 80 lines             |
| `SPEC.md`    | Human + agent     | On demand      | Constraints + structural anchor | Soft 400, hard 800     |
| `README.md`  | New contributor   | On demand      | Onboarding, "how do I run this" | < 150 lines            |

If a piece of information fits in two files, it goes in exactly one.

## Where SPEC.md lives

**Co-located with the code it describes.** A SPEC.md sits in the directory whose contents it explains. Its scope is the subtree rooted at that directory.

- One SPEC.md per *coherent subsystem*, not one per package.
- A subsystem is "the smallest scope where the constraints stop being self-evident from the code."
- The repo root has no SPEC.md. The root has `README.md` and `CLAUDE.md`.
- Cross-cutting documentation (e.g. an operational runbook spanning multiple services) lives in a parent-directory SPEC.md (e.g. `docker/SPEC.md` covers the multi-service stack) or as a top-level special file at the root.
- There is no `docs/` directory in this repo.

## Sections

Every SPEC.md MUST have these three sections, in this order:

1. `## What this is` — one paragraph. A reader who has never seen this code should be able to place it in the system after reading it.
2. `## Shape` — the structural narrative. Moving parts, entry points, file references. The anchor that the constraints attach to. Diagrams optional and constrained (see "Diagrams" below).
3. `## Constraints` — the actual point of the document. The non-obvious choices, the discovered invariants, the things a reader would otherwise have to reverse-engineer from `git log` or rediscover the hard way.

One optional section, used only when it carries content:

- `## See also` — links to other SPECs, external references. Two sentences max per link, explaining why each one matters.

These four (What this is, Shape, Constraints, See also) are the entire allowed vocabulary. Don't add others, even if they seem useful — the common temptations (Known issues, In flight, Future Work, TODO, Glossary, Contributing) all belong elsewhere; see Anti-patterns below for where.

If there are no genuine constraints worth memorializing, the SPEC has no reason to exist — delete it, the code is self-describing. Constraints is the load-bearing section; What this is and Shape exist to anchor it. A subsystem with a clean file layout but no non-obvious constraints does not earn a SPEC.

## Writing constraints

Most constraints are a paragraph or a bullet in `## Constraints`. Plain prose is the default — keep the friction low.

Use the structured form below only when all three paragraphs (context, constraint, consequences) are genuinely carrying weight — typically when alternatives were considered and the reader needs that context to understand why the current shape is what it is:

    ### LightGlue over SuperGlue
    **Context:** [one paragraph — why this came up, what alternatives existed]
    **Constraint:** [one paragraph]
    **Consequences:** [one paragraph, including trade-offs accepted]

The SPEC is a snapshot of present truth. There is no Status field, no supersession chain, no historical tombstones. Constraints are edited in place when they change; deleted when they stop applying. If a new constraint exists *because* an older one didn't work, fold that into the new constraint's Context paragraph — don't preserve the dead one. Git log is the audit trail.

## Length

**Soft cap: 400 lines. Hard cap: 800 lines.**

- Under 400: no justification needed.
- 400–800: the first paragraph after `## What this is` must briefly state why this subsystem is genuinely complex enough to need the extra length. One sentence suffices. The justification exists to discourage drift, not to block real complexity.
- Over 800: split. Either the subsystem isn't one subsystem, or some content belongs in a parent-dir SPEC or a top-level file.

Most SPEC.md files in this repo should land between 80 and 250 lines.

## What goes where

Decision tree. First match wins.

1. Hard rule the agent must follow every turn? → `CLAUDE.md`.
2. Command, path, or env var needed fast? → `CLAUDE.md` (catalog form).
3. New contributor needs it to run the thing in 10 minutes? → `README.md`.
4. A constraint on the subsystem — authored choice or discovered invariant — that won't be obvious from reading the code? → `## Constraints` in the relevant SPEC.md.
5. Active work that will reshape the subsystem? → `.pulsar/memories/<slug>.md`. The memory closes out by folding its findings back into the SPEC.
6. A known bug? → the bug tracker (or a memory if not yet ticketed).
7. Self-evident from 30 seconds of code reading? → No doc.
8. Comment shorter than the surrounding code, rationale is local? → Inline comment.

## Status / lifecycle markers

**No status markers anywhere — not on the doc, not on individual constraints.** The whole document describes the current state of the code. If part of it is stale, that's a bug in the doc, not a status to declare.

This rejects the spec-driven-development pattern that uses status as an ownership signal. It also rejects the ADR pattern of preserving superseded decisions in-place with a status marker. Placeframe is augmentation-first; the code is the source of truth, the SPEC describes it as it is *now*, and git log carries the history.

## Diagrams

**ASCII art only. No mermaid. No PNGs. No embedded images of any kind.**

ASCII renders the same in every viewer — GitHub web, VS Code, terminal `cat`, agent file-reads, raw markdown source. Mermaid renders in some viewers and shows raw syntax in others, so the diagram you authored isn't what every reader sees. PNGs drift silently — the source tool is elsewhere, the export is stale within months.

Example of an acceptable diagram:

    Capture --[tar.gz]--> API --[enqueue]--> Reconstructor --> MinIO
                                                                ^
                                              Localizer --------'

If a system flow can't be sketched in 4–6 lines of ASCII, prose is probably the better tool. Don't draw elaborate diagrams; describe the relationships instead.

## Drift: detection and resolution

The repo answers "what is true?" this way: if SPEC.md and code disagree, the SPEC is wrong by default — *unless* the disagreement is with a deliberately authored constraint (prose or structured) in `## Constraints`. In that case the code might be the bug: the constraint was written down precisely because the shape it preserves isn't self-evident from the code. The fix is to either bring the code back into compliance or rewrite the constraint to reflect the new reality — both are deliberate choices, never a silent drift.

The structured form (Context + Constraint + Consequences) is a presentation choice for constraints that need three paragraphs to land. It carries no more authority than a one-line prose constraint.

**Drift mitigation is co-location + spec-first-on-disagreement. That's all.**

- **Co-location** means a SPEC.md in the same directory as the code is visible in every PR that touches the code. The visual proximity is the signal.
- **Spec-first-on-disagreement** (a rule in root `CLAUDE.md`): when SPEC.md and code disagree, the agent updates the SPEC first to reflect the *intended* state, surfaces the diff, then changes the code. This converts silent drift into an explicit human decision.

Whoever notices drift — agent or human — fixes it. No formal process. No PR checklists. No periodic audits. No drift tickets. The discipline lives in the conventions, not in scaffolding.

## Authoring rules

- **Reference, don't recapitulate.** Link to file paths with `path:line` when pointing at code. No code blocks longer than 8 lines unless the exact text is load-bearing.
- **Write declaratively.** "We will" / "currently" / "for now" rots. Describe the system as it is.
- **Self-contained.** No "see TDD doc" / "as discussed in #channel" pointers — inline the rationale or delete the sentence.
- **The no-docstrings rule does not apply here.** SPEC.md is prose by design. The no-docstrings rule is about source files.
- **No forward pointers into volatile artifacts.** A SPEC must not link to a specific memory, ticket, or bug ID. Those move and close; the SPEC outlives them. The cross-reference direction is one-way: memories and tickets link *to* the SPEC, never the other way around.

## Composing with CLAUDE.md in the same directory

When a directory has both files:

- `CLAUDE.md` is loaded automatically. Keep it terse, imperative, rule-shaped. Cross-reference to SPEC.md for the *why* rather than duplicate rationale.
- `SPEC.md` is loaded on demand. CLAUDE.md may say "before changing the reconstructor pipeline, read SPEC.md."
- Each piece of information lives in exactly one of the two files.

The split is rule (must follow) vs. constraint (must understand).

## Anti-patterns

These have surfaced repeatedly in the literature; don't reintroduce them.

- **"Future Work" section.** Rots within a sprint.
- **"Known issues" section.** Bugs have their own lifecycle; mixing them into a narrative doc means the doc rots every time a bug opens or closes. Use the bug tracker.
- **"In flight" section.** Active work is unstable. Track it in `.pulsar/memories/`; let the memory fold its findings into the SPEC when the work lands.
- **"Glossary" section.** Industry-standard terms (Kalman gain, PnP, BA, Sim3d) have priors a reader already brings; project-coined terms (reconstructor, capture tool) deserve a paragraph of context at first use in Shape, not a one-liner. Glossaries also rot independently of the prose that uses the terms, which makes a stale glossary worse than no glossary. Define inline at first use.
- **Status frontmatter on the doc itself.** Either the doc is true or it's wrong; "draft" is an excuse not to fix it.
- **Embedded diagrams as PNGs or mermaid.** Drift hazard. ASCII only.
- **One enormous root-level SPEC.md.** Split by subsystem.
- **Sibling `DECISIONS.md` / `CONSTRAINTS.md` files.** Constraints live in the SPEC. If the SPEC's constraint list is long, the SPEC is long — that's the SPEC doing its job, bounded by the 800-line cap.
- **Treating SPEC.md as a spec-driven-development source-of-truth** (i.e. code generated from spec). The code is the source of truth.
- **One big "living architecture document"** at the org level. Architecture evolves; one big doc rots. Subsystem-scoped SPECs decay gracefully.
- **External process gates** (PR review checklists, periodic audit owners, drift-tracking tickets). Out of scope. If a rule can't survive on co-location and convention alone, the rule doesn't exist in this repo.
- **Forward links from SPEC to memories or tickets.** Volatile artifacts close; SPECs outlive them. Cross-reference one-way: memory/ticket → SPEC.

## When to delete a SPEC.md

If, walking past it, you can't honestly say it earns its budget — delete it. A wrong SPEC.md is worse than no SPEC.md. The code is always there.
