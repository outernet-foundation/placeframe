---
id: T54
title: Kanban board visual polish (Linear-style)
status: in-review
depends_on: []
plan: t54-plan.md
---

# T54: Kanban board visual polish (Linear-style)

## Goal

Apply CSS-level refinements to the board so it feels like a professionally designed dark UI (Linear-style), not just a functional one. All changes are independently cherry-pickable.

## Context

Research report: `.pulsar/research/kanban-board-polish.md`

The board is functionally complete and already looks good. The research identified 13 specific refinements ranked by impact-to-effort ratio, plus 8 consistency/accessibility issues in the current CSS. The gap is primarily micro-interactions (missing transitions, no hover lift, no focus rings) and small spacing/typography details.

## Key files

- `apps/sveltekit/board/src/app.css` — theme custom properties, global styles
- `apps/sveltekit/board/src/lib/components/Card.svelte` — hover lift, transitions, focus ring
- `apps/sveltekit/board/src/lib/components/Column.svelte` — transition consistency, epic button polish
- `apps/sveltekit/board/src/lib/components/DetailPanel.svelte` — backdrop blur, fix undefined accent-500
- `apps/sveltekit/board/src/lib/components/SearchBar.svelte` — hover state, transition
- `apps/sveltekit/board/src/routes/+page.svelte` — tracking-tight on title, select hover

## Approach

All 13 items from the research report, grouped into 7 logical commits: CSS cleanup, transition consistency, focus-visible rings, card micro-interactions, input polish, spacing/typography, detail panel. Pure CSS class changes — no structural changes, no new files. Full plan in `.pulsar/plans/t54-plan.md`.

## Done when

### Verifiable now
- All interactive elements have `transition-colors` or `transition-all`
- All button/interactive elements have `focus-visible` ring styling
- Card hover includes subtle lift (`-translate-y-0.5`)
- SearchBar and select have hover states
- No undefined color references (`accent-500` replaced)
- Dead CSS custom properties removed
- Linting passes (`pnpm --dir apps/sveltekit/board lint`)
- Type checking passes (`pnpm --dir apps/sveltekit/board check`)

### Requires manual verification
- Board feels noticeably more polished in the browser
- Transitions feel smooth and responsive, not sluggish or abrupt
- Focus rings are visible and themed appropriately

## Log

Clean implementation, no issues. All 13 changes were mechanical CSS class edits. Lint, type check, and 41 unit tests passed on first run. Process finding: the workon skill and spec-format.md lacked guidance on treating visual behaviors as spec-worthy behaviors, which led to nearly skipping the SPEC.md update. Both files were updated to fix this gap.
