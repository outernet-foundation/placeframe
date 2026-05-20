# Placeframe SPEC.md Style Guide

A SPEC.md is the narrative companion to a directory of code. It answers "why is the code shaped this way, what's broken, what's in flight" for a human reader (engineer or AI agent in research mode). It is loaded on demand, not on every turn.

This guide is opinionated. Where the field disagrees, this repo picks one.

## The three-file model

| File         | Audience          | Loaded         | Tone                            | Length budget          |
|--------------|-------------------|----------------|---------------------------------|------------------------|
| `CLAUDE.md`  | AI agent          | Every turn     | Imperative rules, commands      | < 80 lines             |
| `SPEC.md`    | Human + agent     | On demand      | Narrative, descriptive          | Soft 400, hard 800     |
| `README.md`  | New contributor   | On demand      | Onboarding, "how do I run this" | < 150 lines            |

If a piece of information fits in two files, it goes in exactly one.

## Where SPEC.md lives

**Co-located with the code it describes.** A SPEC.md sits in the directory whose contents it explains. Its scope is the subtree rooted at that directory.

- One SPEC.md per *coherent subsystem*, not one per package.
- A subsystem is "the smallest scope where the design rationale stops being self-evident from the code."
- The repo root has no SPEC.md. The root has `README.md` and `CLAUDE.md`.
- Cross-cutting documentation (e.g. an operational runbook spanning multiple services) lives in a parent-directory SPEC.md (e.g. `docker/SPEC.md` covers the multi-service stack) or as a top-level special file at the root (e.g. `DEBUGGING.md`).
- There is no `docs/` directory in this repo.

## Required sections

Every SPEC.md MUST have these three sections, in this order:

1. `## What this is` — one paragraph. A reader who has never seen this code should be able to place it in the system after reading it.
2. `## Shape` — the structural narrative. Moving parts, entry points, file references. Diagrams optional and constrained (see "Diagrams" below).
3. `## Rationale` — the *why*. The non-obvious choices, the trade-offs, the things a reader would otherwise have to reverse-engineer from `git log`.

If you can't fill all three meaningfully, you don't need a SPEC.md. Delete it; the code is self-describing. This rule self-enforces — subsystems without genuine rationale don't get a SPEC rather than getting a hollow one.

## Optional sections

Use these only when there's content. Empty sections are noise.

- `## Known issues` — bugs you know about. One sentence each.
- `## In flight` — work actively underway that will reshape this subsystem. Delete the section when the work lands.
- `## Decisions` — decision log (see "Decisions" below).
- `## See also` — links to other SPECs, external references. Two sentences max per link, explaining why each one matters.

Forbidden sections: "Future work", "TODO list", "Glossary", "Contributing".

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
4. The *why* behind a design choice, or current shape of a subsystem? → `SPEC.md`.
5. Single decision with alternatives considered? → `## Decisions` block in the relevant SPEC.md (or sibling `DECISIONS.md` for high-volume subsystems — see below).
6. Self-evident from 30 seconds of code reading? → No doc.
7. Comment shorter than the surrounding code, rationale is local? → Inline comment.

## Decisions

Decisions live as numbered entries in `## Decisions` in the relevant SPEC.md, **up to the 2nd decision per subsystem.**

    ### D1 — Use LightGlue over SuperGlue (2025-09)
    **Status:** accepted
    **Context:** [one paragraph]
    **Decision:** [one paragraph]
    **Consequences:** [one paragraph, including trade-offs accepted]
    **Superseded by:** D7 (when applicable)

**At the 3rd decision** — or when the existing decision log would push the SPEC past 250 lines, whichever comes first — split the decision log into a sibling `DECISIONS.md` in the same directory. Cross-reference where needed: the SPEC's `## Rationale` may say "see DECISIONS.md §D4" when a current-shape claim depends on a past decision.

Rationale for inline-by-default: most subsystems in this repo will never accumulate three decisions. Inline keeps the friction low and ensures every SPEC reader sees the decisions that exist. The 3rd-decision split prevents bloat without preemptive factoring.

**Supersession:** never edit an accepted decision. Add a new entry, mark the old one `Status: superseded by Dn`. This preserves the historical record.

## Status / lifecycle markers

**No frontmatter, no badges on SPEC.md itself.** The whole document describes the current state of the code. If part of it is stale, that's a bug in the doc, not a status to declare.

Statuses *do* apply to individual `## Decisions` entries: `proposed | accepted | superseded | rejected` (Fowler's canonical four).

This rejects the spec-driven-development pattern that uses status as an ownership signal. Placeframe is augmentation-first; the code is the source of truth, the SPEC describes it.

## Diagrams

**ASCII art only. No mermaid. No PNGs. No embedded images of any kind.**

ASCII renders the same in every viewer — GitHub web, VS Code, terminal `cat`, agent file-reads, raw markdown source. Mermaid renders in some viewers and shows raw syntax in others, so the diagram you authored isn't what every reader sees. PNGs drift silently — the source tool is elsewhere, the export is stale within months.

Example of an acceptable diagram:

    Capture --[tar.gz]--> API --[enqueue]--> Reconstructor --> MinIO
                                                                ^
                                              Localizer --------'

If a system flow can't be sketched in 4–6 lines of ASCII, prose is probably the better tool. Don't draw elaborate diagrams; describe the relationships instead.

## Drift: detection and resolution

The repo answers "what is true?" in this order:

1. **The code.** If SPEC.md and code disagree, the code wins by default and the SPEC is wrong.
2. **A `## Decisions` entry with `Status: accepted`.** If the code contradicts an accepted decision and no superseding decision exists, the *code* is the bug — fix the code, or write a superseding decision.

**Drift mitigation is co-location + spec-first-on-disagreement. That's all.**

- **Co-location** means a SPEC.md in the same directory as the code is visible in every PR that touches the code. The visual proximity is the signal.
- **Spec-first-on-disagreement** (a rule in root `CLAUDE.md`): when SPEC.md and code disagree, the agent updates the SPEC first to reflect the *intended* state, surfaces the diff, then changes the code. This converts silent drift into an explicit human decision.

Whoever notices drift — agent or human — fixes it. No formal process. No PR checklists. No periodic audits. No drift tickets. The discipline lives in the conventions, not in scaffolding.

## Authoring rules

- **Reference, don't recapitulate.** Link to file paths with `path:line` when pointing at code. No code blocks longer than 8 lines unless the exact text is load-bearing.
- **Write declaratively.** "We will" / "currently" / "for now" rots. Describe the system as it is.
- **Self-contained.** No "see TDD doc" / "as discussed in #channel" pointers — inline the rationale or delete the sentence.
- **The no-docstrings rule does not apply here.** SPEC.md is prose by design. The no-docstrings rule is about source files.

## Composing with CLAUDE.md in the same directory

When a directory has both files:

- `CLAUDE.md` is loaded automatically. Keep it terse, imperative, rule-shaped. Cross-reference to SPEC.md for the *why* rather than duplicate rationale.
- `SPEC.md` is loaded on demand. CLAUDE.md may say "before changing the reconstructor pipeline, read SPEC.md."
- Each piece of information lives in exactly one of the two files.

The split is rule (must follow) vs. narrative (must understand).

## Anti-patterns

These have surfaced repeatedly in the literature; don't reintroduce them.

- **"Future Work" section.** Rots within a sprint.
- **Status frontmatter on the doc itself.** Either the doc is true or it's wrong; "draft" is an excuse not to fix it.
- **Embedded diagrams as PNGs or mermaid.** Drift hazard. ASCII only.
- **One enormous root-level SPEC.md.** Split by subsystem.
- **Preemptive `DECISIONS.md` for a subsystem with only one or two decisions.** Inline until the 3rd.
- **Treating SPEC.md as a spec-driven-development source-of-truth** (i.e. code generated from spec). The code is the source of truth.
- **One big "living architecture document"** at the org level. Architecture evolves; one big doc rots. Subsystem-scoped SPECs decay gracefully.
- **External process gates** (PR review checklists, periodic audit owners, drift-tracking tickets). Out of scope. If a rule can't survive on co-location and convention alone, the rule doesn't exist in this repo.

## When to delete a SPEC.md

If, walking past it, you can't honestly say it earns its budget — delete it. A wrong SPEC.md is worse than no SPEC.md. The code is always there.
