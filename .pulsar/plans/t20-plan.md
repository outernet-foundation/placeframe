# T20 Plan: Playwright E2E testing for board app

## Context

During T16, drag-and-drop bugs shipped that passed all jsdom unit tests. Playwright runs a real browser and can test interactions that are structurally invisible to jsdom.

## Approach

### 1. Install Playwright

In `apps/sveltekit/board/`: `pnpm add -D @playwright/test` and `pnpm exec playwright install chromium`.

### 2. Add `BOARD_TICKETS_DIR` env var override to `tickets-dir.ts`

Change the hardcoded path to: `process.env["BOARD_TICKETS_DIR"] ?? path.resolve(process.cwd(), "../../../.pulsar/tickets")`. This lets tests point at a fixture directory without touching real ticket files.

### 3. Add `data-testid` attributes to components

- **Column.svelte**: `data-testid="column-{status}"` on the column root div
- **Card.svelte**: `data-testid="card-{ticket.id}"` on the button element

### 4. Create `playwright.config.ts`

Chromium-only (headless), `webServer` config to auto-start `pnpm dev` with `BOARD_TICKETS_DIR` pointing to fixture dir, test dir `e2e/`, html reporter.

### 5. Test fixture system (`e2e/fixtures.ts`)

- 6 fixture tickets covering all 5 statuses (two in `ready` for multi-card testing), one with dependencies
- `writeFixtureTickets()` writes markdown files to a temp dir
- `resetFixtureTickets()` restores original state after DnD mutation
- `dragCardToColumn()` helper: pointer event sequence (mousedown → mousemove with steps → mouseup → wait for network)

### 6. Global setup/teardown

- `e2e/global-setup.ts`: Creates fixture dir, writes fixture files
- `e2e/global-teardown.ts`: Removes fixture dir

### 7. Test files (3 files, ~18 tests)

**`e2e/board.test.ts`** — Board rendering (5 tests): column rendering, labels/counts, card content, dependency badges, numeric sort order.

**`e2e/drag-and-drop.test.ts`** — DnD with persistence (3 tests): ticket moves to new column, status persists after reload, column counts update.

**`e2e/detail-panel.test.ts`** — Detail panel and search (10 tests): panel open/close (3 methods), content display, markdown rendering, resize, search by title/ID, empty search results.

### 8. Package.json and .gitignore

Add `"test:e2e": "playwright test"` script. Add `test-results/`, `playwright-report/`, `/blob-report/` to gitignore.

### 9. CLAUDE.md update

Add browser install note to environment notes.

## Key files

- `apps/sveltekit/board/src/lib/server/tickets-dir.ts` — add env var override
- `apps/sveltekit/board/src/lib/components/Column.svelte` — add data-testid
- `apps/sveltekit/board/src/lib/components/Card.svelte` — add data-testid
- `apps/sveltekit/board/playwright.config.ts` — new
- `apps/sveltekit/board/e2e/fixtures.ts` — new
- `apps/sveltekit/board/e2e/global-setup.ts` — new
- `apps/sveltekit/board/e2e/global-teardown.ts` — new
- `apps/sveltekit/board/e2e/board.test.ts` — new
- `apps/sveltekit/board/e2e/drag-and-drop.test.ts` — new
- `apps/sveltekit/board/e2e/detail-panel.test.ts` — new
- `apps/sveltekit/board/package.json` — add test:e2e script

## Key technical details

**DnD helper**: `svelte-dnd-action` activates on pointer events with ~3px movement threshold. The helper gets bounding boxes, does mousedown on source, mousemove in 10 steps to target, mouseup, then waits for the PATCH request to complete.

**Resize helper**: Get the `cursor-col-resize` element, mousedown (triggers `pointerdown` + `setPointerCapture`), mousemove horizontally, mouseup, assert width via computed style.

**Test data reset**: `beforeEach` rewrites fixture files. SvelteKit dev server reads files on each SSR request so always sees current state.

## Verification

```bash
cd apps/sveltekit/board
pnpm test:e2e          # All E2E tests pass
pnpm test              # Existing unit tests still pass
pnpm check             # TypeScript still compiles
pnpm lint              # ESLint still passes
```
