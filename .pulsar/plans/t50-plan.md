# T50 Implementation Plan: Board UI Epic Grouping

## Context

The board app is a flat kanban — tickets from different epic subdirectories (board/, ci/, zed/) all mix together with no visual distinction. This ticket adds epic awareness: colored chips on cards, a URL-driven epic filter, and collapsible epic sections within columns. The data layer additions (deriveEpic, collectEpics, groupByEpic) are designed as reusable utilities for future views beyond kanban.

## Approach

### 1. Data layer — add `epic` field and utilities

**`src/lib/tickets.ts`**

- Add `epic: string | null` to the `Ticket` interface.
- Add `deriveEpic(filePath, ticketsDirectory)` — computes `path.relative()`, returns the first path segment if nested, else `null`.
- In `loadTicket()`, set `epic: null` (no directory context when called standalone).
- In `loadTickets()`, after calling `loadTicket(filePath)`, set `ticket.epic = deriveEpic(filePath, directory)`.
- Add `collectEpics(tickets)` — returns sorted unique epic names (excludes null).
- Add `EpicGroup` interface `{ epic: string | null; tickets: Ticket[] }` and `groupByEpic(tickets)` — groups tickets by epic, sorts named epics alphabetically with null last. This is consumed by Column for collapsible sections.

### 2. Epic color utility

**`src/lib/epic-colors.ts`** (new file)

- Map of known epic names → oklch colors (board, ci, zed, specs, skills-audit).
- `epicColor(epic: string): string` — returns known color or generates a deterministic one via string hash → hue.
- Returns an oklch string usable as inline `style` (dynamic value, appropriate per conventions).

### 3. Theme tokens

**`src/app.css`**

- Add `--color-epic-*` tokens for the 5 known epics inside `@theme`. These serve as reference values; the runtime uses the `epicColor()` function for dynamic resolution.

### 4. Server load — return epics list

**`src/routes/+page.server.ts`**

- Add `epics: collectEpics(tickets)` to the returned data, alongside the existing `columns`.

### 5. Card.svelte — epic chip

- Import `epicColor` from `$lib/epic-colors.js`.
- After the ticket ID `<span>`, conditionally render a colored chip when `ticket.epic` is not null.
- Chip: `rounded-full px-2 py-0.5 text-[10px]` with `style="background-color: {epicColor(ticket.epic)}"`.
- `data-testid="epic-chip-{ticket.epic}"` for E2E.
- Root tickets (null epic) show no chip.

### 6. Column.svelte — collapsible epic sections

This is the most complex change:

- Import `groupByEpic` from `$lib/tickets.js` and `epicColor`.
- `epicGroups = $derived(groupByEpic(tickets))` — reactive grouping.
- `collapsedEpics = $state(new Map<string | null, boolean>())` — collapse state, default expanded.
- Render epic subheaders as `<button>` elements with: color dot, ▼/▶ toggle arrow, epic name, ticket count.
- Named epics always show subheaders. The null "ungrouped" group shows a subheader only when multiple groups exist (if all tickets are ungrouped, no subheader — preserves current behavior).
- Cards under collapsed sections are hidden.
- Drag-and-drop remains unchanged — drops change status, not epic (epic is file-path-derived).
- `data-testid="epic-section-{epic}"` / `"epic-section-ungrouped"` for E2E.
- Svelte 5 Map reactivity: create new Map on toggle (`collapsedEpics = new Map(collapsedEpics)`).

### 7. +page.svelte — epic filter dropdown + URL state

- Import `page` from `$app/state` (SvelteKit 2.50+ / Svelte 5 pattern).
- `epicFilter = $derived(page.url.searchParams.get("epic"))`.
- Combine epic filter with search filter in `filteredColumns` (AND logic).
- Add `<select>` dropdown in header after SearchBar, styled to match. Options: "All epics" (value="") + one per `data.epics`.
- `handleEpicChange` uses `goto(url, { replaceState: true, noScroll: true })` to update URL without navigation.
- `data-testid="epic-filter"` on the select.

### 8. E2E fixture updates

**`e2e/fixtures.ts`**

- Add optional `subdirectory?: string` to `FixtureTicket`.
- Add 2 new fixture tickets: T7 (ci epic, status "ready") and T8 (board epic, status "blocked").
- Update `writeFixtureTickets` to create subdirectory when `subdirectory` is set.

**Existing test adjustments:**
- `board.test.ts` line 47: ready column card count 2 → 3
- `drag-and-drop.test.ts` line 63: ready count "2" → "3", line 68: "1" → "2"

### 9. New E2E tests

**`e2e/epic-filter.test.ts`** (new file)

Tests for:
- Epic chips visible on epic tickets, absent on root tickets
- Filter dropdown selects an epic → only that epic's tickets visible
- "All epics" shows everything
- URL contains `?epic=ci` after selection
- Loading `/?epic=ci` applies filter on page load
- Collapsible epic sections visible in columns with mixed groups
- Collapse/expand toggle hides/shows cards

## Key files

| File | Change |
|------|--------|
| `src/lib/tickets.ts` | Add `epic` field, `deriveEpic`, `collectEpics`, `groupByEpic` |
| `src/lib/tickets.test.ts` | Unit tests for new functions, update existing ticket literals |
| `src/lib/epic-colors.ts` | New: epic-to-color mapping utility |
| `src/app.css` | Add `--color-epic-*` tokens |
| `src/lib/components/Card.svelte` | Add colored epic chip |
| `src/lib/components/Column.svelte` | Collapsible epic sections |
| `src/routes/+page.svelte` | Epic filter dropdown, URL state |
| `src/routes/+page.server.ts` | Return `epics` list |
| `e2e/fixtures.ts` | Add subdirectory fixture tickets |
| `e2e/epic-filter.test.ts` | New E2E test file |
| `e2e/board.test.ts` | Update card count assertions |
| `e2e/drag-and-drop.test.ts` | Update count assertions |

## Verification

1. `pnpm --dir apps/sveltekit/board test` — unit tests pass
2. `pnpm --dir apps/sveltekit/board check` — svelte-check passes
3. `pnpm --dir apps/sveltekit/board lint` — ESLint passes
4. `pnpm --dir apps/sveltekit/board test:e2e` — Playwright E2E tests pass (if browser available)
5. Manual: dev server shows chips, filter works, URL state persists, collapse/expand works, DnD still works
