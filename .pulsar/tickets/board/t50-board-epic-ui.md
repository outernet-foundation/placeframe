---
id: T50
title: Board UI epic grouping
status: in-review
depends_on: []
plan: t50-plan.md
---

# T50: Board UI epic grouping

## Goal

Add epic awareness to the board app — both in the data model and the UI — so tickets are visually grouped by their epic subdirectory. Design the epic-aware data layer as a foundation for future views (list, dependency graph, roadmap) beyond the current kanban.

## Context

Epic subdirectories already exist under `.pulsar/tickets/` (`board/`, `ci/`, `zed/`, `specs/`, `skills-audit/`). The data layer (`loadTickets()`) already recursively scans them and preserves `filePath` on each ticket. What's missing is:

1. **Data model** — the `Ticket` interface has no `epic` field. The epic can be derived from `filePath` (parent directory name, or `null` for root-level tickets), but nothing does this yet.
2. **UI** — the board has no awareness of epics. No badges, no filtering, no grouping.

This is the first step toward the board becoming a multi-view project tool rather than a flat kanban. The epic-aware data layer should be designed so that a future list view, dependency graph, or epic roadmap view can consume the same grouped data without rearchitecting.

### Current ticket distribution by epic

- `board/` — 8 tickets (T20, T22–T25, T50, T51, T52)
- `ci/` — 8 tickets (T1–T8)
- `zed/` — 4 tickets (T10–T13)
- `specs/` — 1 ticket
- `skills-audit/` — 1 ticket
- root (ungrouped) — ~10 tickets

### What this is NOT

- Not adding new frontmatter fields — epic identity comes from directory structure, not metadata.
- Not adding EPIC.md files or epic-level configuration — keep it simple.
- Not building other views yet — just making the kanban epic-aware and ensuring the data layer supports future views.

## Key files

- `apps/sveltekit/board/src/lib/tickets.ts` — add `epic` field to Ticket interface, derive from filePath
- `apps/sveltekit/board/src/lib/components/Card.svelte` — show epic badge
- `apps/sveltekit/board/src/lib/components/Board.svelte` — potential layout changes for grouping
- `apps/sveltekit/board/src/routes/+page.svelte` — epic filter control

## Approach

Design decisions (resolved):

1. **Filter + visual grouping** — epic dropdown in the header filters by epic. When showing all epics, tickets are visually grouped within columns.
2. **Colored chip** — small pill/chip next to the ticket ID on each card, colored per epic. Root-level tickets show no chip.
3. **URL query param** — `?epic=board` for shareable, bookmarkable filter state via `$page.url.searchParams`.
4. **Collapsible epic sections** — within each status column, tickets are grouped under collapsible epic subheaders (e.g. "▼ board (2)"). Collapse state is client-side only. Epics with no tickets in a column are omitted.
5. **"All" default** — no filter active = show all tickets with epic grouping. Filter narrows to one epic.

## Done when

- Ticket interface has an `epic` field (string | null, derived from directory path)
- Board cards show which epic they belong to (badge, chip, or similar)
- User can filter the board to show only tickets from a specific epic
- Ungrouped (root-level) tickets display cleanly without an epic label
- Existing unit tests and E2E tests still pass
- New E2E test verifies epic filtering works

## Log

- **SvelteMap reactivity**: Initially used `SvelteMap<string | null, boolean>` for collapse state. The `.get()` calls in the template didn't reliably trigger re-renders. Switched to `SvelteSet<string>` with a `collapseKey()` helper (maps `null` → `"__ungrouped"`). SvelteSet's `.has()` tracks correctly.
- **`$state({})` property additions**: Tried plain `$state` object for collapse. Setting a new property (`collapsed[key] = true` where key didn't exist) didn't trigger reactivity. Svelte 5's proxy doesn't track property additions on objects — only mutations to existing properties. SvelteSet avoids this.
- **`window.history.replaceState` conflicts with SvelteKit**: Initially used `window.history.replaceState` for URL updates. SvelteKit warns this conflicts with its router. Switched to `pushState` from `$app/navigation`.
- **ESLint `no-navigation-without-resolve` rule**: Required wrapping the URL arg to `pushState`/`goto`/`replaceState` with `resolve()` from `$app/paths`. Since `resolve()` only accepts typed route IDs (not query strings), used `as "/"` cast for the path with query params — `resolve` just prepends the base path, so the cast is safe at runtime.
- **E2E hydration timing**: Tests failed because `page.goto("/")` returns before Svelte 5 hydration completes, so event handlers weren't attached. Added `await page.waitForLoadState("networkidle")` before interactive tests that use `selectOption` or `click`.
