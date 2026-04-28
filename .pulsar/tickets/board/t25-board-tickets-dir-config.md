---
id: T25
title: Configure tickets directory via environment variable
status: design-needed
depends_on: []
---

# T25: Configure tickets directory via environment variable

## Goal

Replace the fragile `path.resolve(process.cwd(), "../../../.pulsar/tickets")` with a configurable approach, such as a SvelteKit `$env` variable.

## Context

The current tickets directory resolution couples the app to being run from a specific working directory. If the app is run from a different location, it silently reads the wrong directory or fails. Identified as a gap during the board SPEC.md backfill.

## Key files

- `apps/sveltekit/board/src/lib/server/tickets-dir.ts` — path resolution

## Approach

To be written during design/plan mode.

## Done when

To be defined after design discussion.
