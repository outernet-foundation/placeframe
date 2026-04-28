---
id: T79
title: "Unity CI: make license activation failures visible"
status: in-review
depends_on: [T7]
---

# T79: Unity CI: make license activation failures visible

## Goal

Make Unity license activation failures in CI visible instead of silently swallowed, so licensing issues (seat limits, server outages, credential rotation) are diagnosed quickly.

## Context

The Unity CI workflow (`unity.yml`) ends the activation step with `|| true`, which swallows all activation errors. The build then proceeds — it may work (cached license), partially work, or fail with a confusing error unrelated to licensing. If the 2-seat serial limit is ever hit (likely when Windows builds are added per T75), the failure will be invisible.

The same `|| true` pattern is used on the return-license step, which is more defensible (we don't want a failed return to mark the whole job as failed), but activation failures should not be silent.

## Key files

- `.github/workflows/build-unity.yml` — activation and return-license steps

## Done when

- License activation step fails the job if activation fails
- Return-license step remains best-effort (`|| true` or `if: always()` with `continue-on-error`)
- Activation errors appear in the job summary or annotations, not just buried in logs

## Log

Clean implementation, no issues.

## Observations

- The ticket's Key files section referenced `unity.yml` but the actual file is `build-unity.yml` (renamed in T78). Updated the reference.
