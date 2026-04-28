---
id: T22
title: Board live refresh on ticket file changes
status: design-needed
depends_on: []
---

# T22: Board live refresh on ticket file changes

## Goal

Update the kanban board to reflect ticket file changes on disk without requiring a manual page reload.

## Context

Currently, if a ticket file is edited outside the board (e.g., via `/workon` or a text editor), the board does not update until the user reloads the page or performs a drag-and-drop (which triggers `invalidateAll`). Identified as a gap during the board SPEC.md backfill.

## Key files

- `apps/sveltekit/board/src/routes/+page.server.ts` — current SSR data loading
- `apps/sveltekit/board/src/routes/+page.svelte` — page layout

## Approach

To be written during design/plan mode.

## Done when

To be defined after design discussion.
