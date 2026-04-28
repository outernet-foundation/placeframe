# T54 Plan: Kanban Board Visual Polish

## Context

The board is functionally complete but needs CSS-level refinements to feel professionally designed. Research report (`.pulsar/research/kanban-board-polish.md`) identified 13 specific changes. All are CSS utility class edits — no new files, no structural changes.

## Approach

Implement all 13 items in 7 grouped commits, working file-by-file. Since these are purely CSS class changes in Svelte templates, skip TDD — verification is lint/check passes plus visual inspection.

### Commit 1: CSS cleanup (`app.css`)
- Remove dead `--color-epic-*` custom properties (lines 24-28) — all epic coloring goes through TypeScript `epicColor()`
- Remove unused `--color-surface-600` (line 8) — same lightness as `border-default`, never referenced
- Add `--color-accent: oklch(0.6 0.15 260)` for the resize handle (replacing undefined `accent-500`)

### Commit 2: Transition consistency (all components)
- **Card.svelte** line 10: `transition-colors` → `transition-all duration-200` (needed for transform lift)
- **Column.svelte** line 85/96: add `transition-colors` to epic section buttons
- **DetailPanel.svelte** line 74: add `transition-colors` to close button
- **DetailPanel.svelte** line 63: add `transition-colors` to resize handle; replace `bg-accent-500/50` → `bg-accent/50`; replace `'bg-accent-500/50'` → `'bg-accent/50'`
- **SearchBar.svelte** line 9: add `transition-colors`
- **+page.svelte** line 68: add `transition-colors` to select

### Commit 3: Focus-visible rings (all interactive elements)
- **Card.svelte**: add `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-900`
- **Column.svelte** epic buttons: add `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-900`
- **Column.svelte** drop zone: add `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-900`
- **DetailPanel.svelte** close button: add same focus-visible pattern with `ring-offset-surface-800` (different bg)
- **SearchBar.svelte**: add `focus-visible:ring-2 focus-visible:ring-white/20` (already has `focus:outline-none`)
- **+page.svelte** select: add same focus-visible pattern

### Commit 4: Card micro-interactions (`Card.svelte`)
- Add hover lift: `hover:-translate-y-0.5`
- Add active press: `active:scale-[0.98] active:duration-75`

### Commit 5: Input polish (`SearchBar.svelte`, `+page.svelte`)
- Add `hover:border-border-default` to SearchBar input
- Add `hover:border-border-default` to epic filter select

### Commit 6: Spacing & typography
- **+page.svelte** line 65: add `tracking-tight` to h1
- **Card.svelte** line 10: `py-3.5` → `py-3` (spacing rhythm)
- **Column.svelte** line 61: `gap-2` → `gap-2.5` (card gap)
- **Board.svelte**: `gap-4` → `gap-6` (column gap)

### Commit 7: Detail panel polish (`DetailPanel.svelte`)
- Backdrop line 49: `bg-black/50` → `bg-black/40 backdrop-blur-sm`

## Key files

- `apps/sveltekit/board/src/app.css` — commits 1
- `apps/sveltekit/board/src/lib/components/Card.svelte` — commits 2, 3, 4, 6
- `apps/sveltekit/board/src/lib/components/Column.svelte` — commits 2, 3, 6
- `apps/sveltekit/board/src/lib/components/Board.svelte` — commit 6
- `apps/sveltekit/board/src/lib/components/DetailPanel.svelte` — commits 2, 3, 7
- `apps/sveltekit/board/src/lib/components/SearchBar.svelte` — commits 2, 3, 5
- `apps/sveltekit/board/src/routes/+page.svelte` — commits 2, 3, 5, 6

## Verification

1. `pnpm --dir apps/sveltekit/board lint`
2. `pnpm --dir apps/sveltekit/board check`
3. `pnpm --dir apps/sveltekit/board test`
4. Manual: visual inspection in browser for transitions, focus rings, hover lift
