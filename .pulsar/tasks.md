# Backlog

## Mode system
- Define plan mode
- Define implement mode
- Define diagnose mode
- Define audit mode
- Define research mode
- Define rebase mode
- Define commit mode — pairs with rebase; scaffolded at `.pulsar/modes/commit.md`, not yet designed

## SPEC→constraints rename
- Design the rename initiative: one guidance file per subtree root, SPEC.md → constraints.md, merging CLAUDE.md + SPEC.md where a subtree has both. Drains the uncommitted constraints in `.pulsar/designs/design-mode.md`
- Verify opencode's auto-load / scoping behaviour for nested guidance files (does it load `constraints.md` by name, or only `CLAUDE.md` / `AGENTS.md`?) — gates whether the rename preserves reliable loading
- Ratify the "one guidance file per subtree root" decision (A2) — currently my recommendation, recorded in `.pulsar/designs/design-mode.md`

## Branch integration
- Integrate the `feature/pulsar-modes` lineage onto `origin/dev` (it is ~32 commits ahead, including the unmerged `e545bb15` "Mass update all CLAUDE.md files"); sort the modes vs relocalization split as part of that
