# T51 Plan: Replace svelte-dnd-action with Native HTML5 Drag-and-Drop

## Context

`svelte-dnd-action` is untestable with Playwright (blocks pointer events, consider/finalize never completes under automation) and adds complexity for a simple column-to-column move. Replacing it with the browser's native HTML5 DnD API eliminates the dependency, simplifies the component architecture, and unblocks T20 (Playwright E2E testing).

## Approach

### 1. Card.svelte — add draggable and ondragstart

Add `draggable="true"` and an `ondragstart` handler to the existing `<button>`. The handler sets `dataTransfer` with the ticket ID (`text/plain`) and `effectAllowed = "move"`. No new props needed — Card already has the `ticket` prop.

Click vs. drag: the browser distinguishes these natively (click fires on mouseup without movement, drag fires when movement threshold is crossed). No special handling needed.

### 2. Column.svelte — replace use:dndzone with native DnD events

- Remove `dndzone` and `DndEvent` imports from `svelte-dnd-action`.
- Replace `onconsider`/`onfinalize` callback props with a single `onticketdrop: (ticketId: string, status: Status) => void`.
- Change `tickets` prop type from `(Ticket & { id: string })[]` to `Ticket[]` (the `& { id: string }` was only needed by svelte-dnd-action).
- Remove `use:dndzone={{ items: tickets, dropTargetStyle: {} }}`.
- Add native event handlers on the card container:
  - `ondragover`: `event.preventDefault()` + set `dropEffect = "move"` (required to allow dropping).
  - `ondrop`: `event.preventDefault()`, reset drag counter, read ticket ID from `dataTransfer`, skip same-column drops (`!tickets.some(t => t.id === ticketId)`), call `onticketdrop(ticketId, status)`.
  - `ondragenter`: `event.preventDefault()`, increment `dragOverCount`.
  - `ondragleave`: decrement `dragOverCount`.
- Add `$state` variable `dragOverCount` (number) and `$derived` `isDragOver` (boolean, `dragOverCount > 0`) for visual feedback.
- Apply conditional CSS: `border-border-default bg-surface-800` when `isDragOver`, `border-border-subtle` otherwise. Uses existing theme tokens with `transition-colors`.

The dragenter/dragleave counter approach handles nested child elements correctly — every child entering/leaving fires events, but the counter only reaches 0 when the cursor truly leaves the container.

### 3. Board.svelte — simplify (remove consider/finalize and columnItems)

- Remove `DndEvent` import from `svelte-dnd-action`.
- Remove `columnItems` derived state entirely (it existed only for svelte-dnd-action's consider-phase mutations).
- Remove `handleConsider` and `handleFinalize` functions.
- Pass `columns[status] ?? []` directly as `tickets` prop.
- Pass `onstatuschange` directly as `onticketdrop` — signatures match exactly: `(ticketId: string, newStatus: Status) => void`.

This reduces Board from 55 lines to ~22 lines — a pure layout pass-through.

### 4. package.json — remove svelte-dnd-action

Remove `"svelte-dnd-action": "^0.9.0"` from `dependencies`. Run `pnpm --dir apps/sveltekit/board install` to update lockfile.

### 5. SPEC.md — update design decision (requires user approval)

Replace the `svelte-dnd-action` design decision bullet with a description of native HTML5 DnD. Also fix column count from "five" to "six" (in-review was added after the original spec).

## Key design decisions

- **`onticketdrop` callback name**: Can't use `ondrop` because Svelte 5 treats `on*` props as DOM event handlers. `onticketdrop` is unambiguous.
- **No optimistic UI during drag**: Card stays in source column during drag; browser provides a ghost image. After drop, `invalidateAll()` reloads data. Simpler than replicating svelte-dnd-action's consider-phase visual.
- **Same-column drops ignored**: Column checks `!tickets.some(t => t.id === ticketId)` before calling `onticketdrop`, avoiding unnecessary PATCH requests.
- **`text/plain` for dataTransfer**: Simplest format. Only one piece of data needed (ticket ID).

## Key files

| File | Action |
|---|---|
| `apps/sveltekit/board/src/lib/components/Card.svelte` | Add `draggable="true"` and `ondragstart` |
| `apps/sveltekit/board/src/lib/components/Column.svelte` | Replace `use:dndzone` with native DnD events + visual feedback |
| `apps/sveltekit/board/src/lib/components/Board.svelte` | Remove consider/finalize, remove columnItems, wire `onticketdrop` |
| `apps/sveltekit/board/package.json` | Remove `svelte-dnd-action` dependency |
| `apps/sveltekit/board/SPEC.md` | Update design decision (user approval required) |

## Verification

1. `pnpm --dir apps/sveltekit/board check` — TypeScript compiles
2. `pnpm --dir apps/sveltekit/board lint` — ESLint passes
3. `pnpm --dir apps/sveltekit/board test` — unit tests pass
4. `grep -r "svelte-dnd-action" apps/sveltekit/board/` — no references remain
5. Manual: drag a card between columns, confirm status persists; click a card, confirm detail panel opens
