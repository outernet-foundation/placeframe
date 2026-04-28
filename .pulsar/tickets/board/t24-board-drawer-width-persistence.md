---
id: T24
title: Persist detail drawer width in localStorage
status: design-needed
depends_on: []
---

# T24: Persist detail drawer width in localStorage

## Goal

Persist the detail panel drawer width across page reloads using localStorage.

## Context

The drawer width is stored in page-level `$state` and resets to 672px on reload. Users who resize the drawer expect it to remember their preference. Identified as a gap during the board SPEC.md backfill.

## Key files

- `apps/sveltekit/board/src/routes/+page.svelte` — drawerWidth state
- `apps/sveltekit/board/src/lib/components/DetailPanel.svelte` — resize logic

## Approach

To be written during design/plan mode.

## Done when

To be defined after design discussion.
