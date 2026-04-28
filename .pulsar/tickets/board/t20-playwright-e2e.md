---
id: T20
title: Playwright E2E testing for board app
status: in-review
depends_on: [T51]
plan: t20-plan.md
---

# T20: Playwright E2E testing for board app

## Goal

Add Playwright end-to-end testing to the SvelteKit board app, covering interaction-level behavior that jsdom-based unit tests fundamentally cannot catch — particularly drag-and-drop between columns.

## Context

During T16 implementation, two bugs shipped that passed all existing tests: tickets not rendering in the UI (a data-to-component wiring issue) and drag-and-drop causing tickets to vanish (an interaction-level bug in the finalize handler). The first class could be caught by component tests in jsdom. The second cannot — jsdom has no layout engine, no real pointer events, and `svelte-dnd-action` relies on actual DOM coordinates.

Playwright runs a real browser and can click, drag, drop, and assert on real layout. The setup cost (browser binaries, CI configuration) is a one-time investment. The app is small today but we're planning for six months from now — if Playwright catches bugs that are structurally invisible to the rest of the test stack, the investment is correct regardless of current app size.

This is the first ticket completed fully under the new spec-aware workflow from T18. The board's SPEC.md (from T19) should be updated (with user approval) to reflect the new testing infrastructure.

## Key files

- `apps/sveltekit/board/playwright.config.ts` — Playwright configuration
- `apps/sveltekit/board/e2e/` — E2E test files
- `apps/sveltekit/board/package.json` — new scripts and devDependencies
- `apps/sveltekit/board/SPEC.md` — updated to reflect E2E testing setup

## Approach

Add Playwright with Chromium-only config, a `BOARD_TICKETS_DIR` env var override for test fixture isolation, `data-testid` attributes on Column and Card components, and three test files (~18 tests) covering board rendering, drag-and-drop with persistence, detail panel interactions, and search filtering. Full plan in `.pulsar/plans/t20-plan.md`.

## Done when

### Verifiable now
- `@playwright/test` is installed as a devDependency
- `playwright.config.ts` exists with sensible defaults (Chromium at minimum)
- pnpm scripts exist for running E2E tests (`pnpm test:e2e` or similar)
- E2E tests cover: ticket rendering in columns, drag-and-drop between columns with persistence, detail panel open/close, detail panel resize, search filtering, markdown rendering in detail panel
- The drag-and-drop test specifically verifies the ticket appears in the new column after drop (the bug that shipped in T16)
- All E2E tests pass
- CLAUDE.md environment notes updated if browser install needs documentation

### Requires manual verification
- Tests run reliably (no flakiness in DnD tests)
- Board SPEC.md updated with user approval to reflect E2E testing setup

## Log

- Initial test run: all detail panel and DnD tests failed. Detail panel tests failed because `page.goto("/")` returns before SvelteKit hydration completes, so `onclick` handlers weren't active. Fixed by adding `page.waitForLoadState("networkidle")` after navigation in interaction tests.
- Playwright's `locator.dragTo()` does not correctly carry `dataTransfer` data for native HTML5 DnD. The drag events fire but `getData("text/plain")` returns empty. Fixed by implementing a `dragCardToColumn()` helper that dispatches synthetic `DragEvent`s with a shared `DataTransfer` object via `page.evaluate()`.
- Escape key test failed because the `onkeydown` handler was on the panel wrapper div which never received focus. Focus stayed on the card button (behind the backdrop). This was a real bug in DetailPanel.svelte — moved the Escape handler to `<svelte:window>` so it fires regardless of focus state.
- Resize test failed for two reasons: (1) measuring handle position during the `fly` transition gave wrong coordinates — fixed by waiting 400ms for transition to complete; (2) `page.mouse` doesn't correctly trigger `setPointerCapture` — fixed by using `dispatchEvent("pointerdown/pointermove/pointerup")` directly on the handle locator.
- Running 3 workers caused fixture interference (shared temp directory + shared dev server). Fixed by setting `workers: 1` in playwright.config.ts.
