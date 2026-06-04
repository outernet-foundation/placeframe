---
updated: 2026-06-02
---

# Dockerfile `base`/`dev`/`prod` stage split is inconsistently applied across Python services

## Goal

The repo has a multi-stage Dockerfile pattern — `base` → (`dev` | `prod`) — whose purpose is to let a developer attach a debugger to a running container and have edits in the local working tree show up live. `dev` does `uv pip install -e ...` (editable) and is paired with a bind mount of source over `/app/...` in `compose.yml`; `prod` does the non-editable install so the published image is self-contained. `compose.bake.yml` pins `target: dev` for the local stack on services that have two targets.

The pattern is currently applied to exactly three services — `api`, `lease-server`, `livekit-token` — and the choice of *which three* doesn't match where debugger attach is actually used. That's the discrepancy to revisit.

## State

- **Has the split** (`base`/`dev`/`prod` in Dockerfile, `target: dev` in `compose.bake.yml` at lines 71/90/100):
  - `docker/api/Dockerfile` — original. Added by commit `bad9df98` ("Miscellaneous fixes and improvements" → "Fixed attach debugging for API (use editable installs for dev, and mount source in compose.yml)"). Authored by Tyler Hatch, Jan 21 2026. **Tyler introduced the pattern**, not Claude.
  - `docker/lease-server/Dockerfile` — added by Claude when scaffolding `lease-server` in the reconstructor-split work, by copying the `api` pattern.
  - `docker/livekit-token/Dockerfile` — added by Claude at some point, by copying the `api` pattern.
- **Lacks the split** but **actively uses debugger attach**:
  - `docker/reconstructor/Dockerfile` — `.env.sample` has `DEBUG_RUN_RECONSTRUCTION_WAIT=true`-style flags.
  - `docker/localizer/Dockerfile` — `.env.sample` has `DEBUG_FEATURES_WAIT=true`-style flags.
  These two install source non-editably and require an image rebuild to pick up edits — defeating attach. This is the real gap.
- **Lacks the split, doesn't need it** (single-shot, runs once and exits): `auth-initializer`, `database-manager`, `database-migrator`, `cloudbeaver-initializer`.
- **N/A**: `gateway` (Caddy), `aoa-gateway` (Caddy), `postgres`, `keycloak`, `loki`, `alloy`, `grafana`, `aoa-loki`, `aoa-alloy`, `neural-networks-base` (build base, not a service).
- **Long-running Python services that *could* take the pattern if attach is ever wanted**: `state-sync`, `aoa-bridge`, `zed-capture`.

## Decisions

None yet — Tyler asked to memorize the discrepancy and revisit later. No edits in flight on this initiative.

Notes that informed the discrepancy framing (not commitments):

- `livekit-token` is 46 lines, no workspace package imports (only third-party `litestar` + `livekit-api`); its `dev` target is essentially `-e /app/docker/livekit-token` only. If nobody attaches a debugger to it, the `dev` stage is dead weight and the file could collapse to a single stage.
- `lease-server` imports the same workspace packages as `api` (`common`, `core`, `datamodels`) and is a long-running Litestar service; the pattern is plausibly justified there.
- The directionally correct cleanup is some mix of (a) stripping `dev`/`prod` from services that won't be attached to, and (b) adding it to `reconstructor` and `localizer` where attach is already wired up via env vars.

## Open questions

- Which services should keep the split? Specifically, do you attach a debugger to `lease-server` or `livekit-token` in practice? If not, those two stage splits are dead code that should be collapsed.
- Add the split to `reconstructor` and `localizer`? Those have `DEBUG_*_WAIT` env knobs in `.env.sample` but the Dockerfiles don't support live source — confirm this is actually friction in your debug workflow before adding stages.
- For `state-sync` / `aoa-bridge` / `zed-capture` — is attach a plausible workflow, or are they fire-and-forget?

## Key files

- `docker/api/Dockerfile` — the canonical example of the pattern (`base` → `dev` → `prod`).
- `docker/lease-server/Dockerfile` — copy of the pattern; questionable necessity.
- `docker/livekit-token/Dockerfile` — copy of the pattern; very likely unnecessary.
- `docker/reconstructor/Dockerfile` — missing the pattern; debug attach is wired in `.env.sample`.
- `docker/localizer/Dockerfile` — missing the pattern; debug attach is wired in `.env.sample`.
- `compose.bake.yml` lines 71, 90, 100 — where `target: dev` is pinned for the three services that have the split.
- `compose.yml` — where source bind mounts are wired for the `dev` target services. Check whether `reconstructor`/`localizer` have analogous mounts or whether those would need to be added too.
- `.env.sample` — contains the `DEBUG_*_WAIT` flags that prove attach is intended for `reconstructor` and `localizer`.
- Commit `bad9df98` — introduced the `api` pattern with the rationale "Fixed attach debugging for API (use editable installs for dev, and mount source in compose.yml)".

## Pending threads

- Decide the target state: which services should have `base`/`dev`/`prod`, which should collapse to one stage, and which should newly gain the split. Drive a single sweep that brings every Python service Dockerfile into line with that decision, rather than leaving the current ad-hoc mix.
- After deciding, also confirm `compose.yml` bind mounts and `compose.bake.yml` `target:` pins are aligned with the new shape.

Additional content the user asked to capture: this specific discrepancy, we'll revisit it later
