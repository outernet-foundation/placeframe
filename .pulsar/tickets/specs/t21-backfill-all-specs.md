---
id: T21
title: Backfill specifications for all subsystems
status: design-needed
depends_on: []
---

# T21: Backfill specifications for all subsystems

## Goal

Create SPEC.md files for all major subsystems in the project, using the backfill workflow from T18 and the board spec (`apps/sveltekit/board/SPEC.md`) as the reference example.

## Context

The spec convention (T18) and the first spec (the board, backfilled under T16) establish the pattern. This ticket extends it across the full project. The effort is large and deferred — this ticket exists to record the decision that comprehensive specs are worth doing, not to do them immediately.

Key open questions that need discussion before planning:

- **Granularity**: One SPEC.md per deployable unit (`docker/api/`, `docker/localizer/`, `scripts/`) seems right as a starting point. But the localizer has distinct subsystems (feature extraction, matching, pose estimation) — should it get sub-specs?
- **Scope**: Which parts of the project need specs? Candidates: API service, localizer service, database schema, CLI scripts, Keycloak configuration, Docker/compose infrastructure. Generated packages (`packages/generated/`) are derived artifacts and probably don't need specs.
- **Interactive discovery**: For subsystems where design decisions live in the user's head (not recoverable from code alone), the backfill flow needs to ask targeted questions. The quality of those questions matters — this ticket should validate that the backfill process from T18 works well for code the user built long before the spec convention existed.
- **Splitting**: This ticket will likely be split into per-subsystem tickets during the design phase.

## Key files

- One SPEC.md per subsystem (exact list TBD during design)

## Approach

To be written during design/plan mode. Will likely be split into multiple tickets.

## Done when

To be defined after design discussion resolves the open questions above.
