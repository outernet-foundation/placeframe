---
id: T51
title: Replace svelte-dnd-action with native HTML5 drag-and-drop
status: done
plan: t51-plan.md
---

# T51: Replace svelte-dnd-action with native HTML5 drag-and-drop

## Goal

Replace the `svelte-dnd-action` library with native HTML5 Drag and Drop API for the board's column-to-column ticket dragging.

## Context

During T20 (Playwright E2E testing), we discovered that `svelte-dnd-action` is effectively untestable with Playwright. The library uses a custom pointer-event-based drag system that:

1. **Blocks card clicks** — the library intercepts `pointerdown` events on items, preventing normal `click` events from reaching Svelte's `onclick` handlers. Playwright's `.click()` doesn't work; only `el.click()` via `evaluate` works (after waiting for hydration).
2. **Cannot be driven by Playwright's mouse API** — multiple approaches were tried (manual `page.mouse` sequences with various timings, Playwright's `locator.dragTo()`, synthetic `PointerEvent` dispatch via `evaluate`). The drag consider phase sometimes activates (item removed from source) but finalize never completes (item never lands in target, PATCH request never fires).
3. **Adds complexity for a simple use case** — the board only needs to move a card between 5 columns. There's no within-column reordering, no nested zones, no touch support needed.

The native HTML5 DnD API (`draggable="true"` + `ondragstart`/`ondragover`/`ondrop`) is sufficient for this use case and has first-class Playwright support via `locator.dragTo()`. Svelte 5 can handle this with plain event attributes — no library needed.

## Key files

- `apps/sveltekit/board/src/lib/components/Column.svelte` — replace `use:dndzone` with native DnD events
- `apps/sveltekit/board/src/lib/components/Board.svelte` — replace consider/finalize handlers with native DnD state
- `apps/sveltekit/board/src/lib/components/Card.svelte` — add `draggable="true"` and `ondragstart`
- `apps/sveltekit/board/package.json` — remove `svelte-dnd-action` dependency

## Approach

Replace `svelte-dnd-action`'s `use:dndzone` directive with native HTML5 DnD:

- **Card.svelte**: Add `draggable="true"`, `ondragstart` sets `dataTransfer` with the ticket ID.
- **Column.svelte**: Replace `use:dndzone` with `ondragover` (prevent default to allow drop), `ondrop` (read ticket ID from `dataTransfer`, call status change handler). Add visual drop-target feedback via `ondragenter`/`ondragleave`.
- **Board.svelte**: Simplify handlers — remove consider/finalize pattern, replace with a single `onstatuschange` flow triggered by the drop event.
- Remove `svelte-dnd-action` from `package.json`.

## Done when

### Verifiable now
- `svelte-dnd-action` is removed from `package.json`
- Dragging a card from one column to another changes its status (persists to disk)
- Card clicks still open the detail panel (no pointer event interference)
- All existing unit tests pass
- TypeScript compiles (`pnpm check`)
- ESLint passes (`pnpm lint`)

### Requires manual verification
- Visual drop-target feedback is clear (user can see where they're dropping)
- Drag feels responsive (no noticeable lag vs the old library)

## Log

- `svelte-check` flagged a11y warning on Column drop target `<div>` with drag handlers: "must have an ARIA role". Added `role="listbox"` + `aria-label`. Second pass flagged "elements with 'listbox' interactive role must have a tabindex value". Added `tabindex="0"`. Zero warnings after that.
- No test failures or wrong approaches otherwise.
