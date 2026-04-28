---
id: T23
title: Board search — add status and dependency filtering
status: design-needed
depends_on: []
---

# T23: Board search — add status and dependency filtering

## Goal

Extend the board's search/filter to support filtering by status and dependency, not just title and ticket ID.

## Context

The current search bar filters cards client-side by title and ticket ID (case-insensitive). Filtering by status or dependency was identified as a gap during the board SPEC.md backfill.

## Key files

- `apps/sveltekit/board/src/routes/+page.svelte` — filter logic
- `apps/sveltekit/board/src/lib/components/SearchBar.svelte` — search input

## Approach

To be written during design/plan mode.

## Done when

To be defined after design discussion.
