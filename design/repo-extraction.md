# Repo boundaries: capture-tool and ZED appliance extraction

## Scope

The repo-boundaries thread of the polyrepo initiative ([index](polyrepo.md)): extract the phone-side capture tool and the ZED box appliance into standalone repos, define the four cross-repo contracts, and hold the fresh-clone-autonomy invariant. Siblings: [prepo, the polyrepo workbench](polyrepo-workbench.md) and [publishing](package-publishing-redesign.md).

## Problem

The capture tool and the ZED appliance become standalone repos. Cross-repo consumption is registry consumption — which makes the publishing thread load-bearing rather than cosmetic: a broken publish no longer costs external visibility, it blocks the other repos' development loops. The extraction is the event that converts sibling consumption from intra-repo `file:` refs to registry pins, and the event that first exercises prepo's dependency overlay.

## Design

### Extraction

| New repo | Takes | Publishes |
|---|---|---|
| capture-tool (name open) | `apps/CaptureTool/`, the `capture-tool-v*` tag prefix, `unity-build.json`, the AOA Java/OkHttp client + handler, the log relays, the `install --project CaptureTool` flow | APKs |
| zed appliance (name open) | `docker/zed-capture/`, `docker/aoa-bridge/`, `docker/aoa-gateway/`, box `loki`/`alloy` configs, `compose.rig.yml`, the zed targets of `compose.zed.bake.yml`, `placeframe-zed.service`, `wait_for_zed_camera.py`, `install-zed` (`scripts/src/scripts/install_zed/`), zed-capture-client generation (openapi-clientgen as a library) | `PlaceframeZedCaptureClient` (nuget + npm), box images (own GHCR namespace) |

placeframe keeps the server stack, the UPM SDK (`Core`, `ARFoundation`, `MagicLeap`, `Auth`, `Logging`), api-client generation, and MapRegistrationTool as an in-repo consumer — the `file:` consumption path stays exercised where it remains intra-repo. The top-level `zed/` tree is dead (its `src/` contains only `__pycache__`): delete it, do not move it.

### Client generation in the zed repo

The zed repo consumes openapi-clientgen as a library for zed-capture-client generation and publishing; placeframe's `generate-clients` drops the zed project entry at cutover.

### Cross-repo contracts

Four contracts become inter-repo. Each gets one authoritative home, referenced — never duplicated — by both sides' agent docs:

1. **Capture tar** (`rig*/frames.csv` + stereo JPEGs + factory calibration) — box → placeframe reconstructor.
2. **zed-capture REST API** — box → phone. The committed `openapi.json` is the machine-checkable artifact and the compat gate; the phone pins a `zedcaptureclient` version.
3. **AOA transport** (h2c prior-knowledge over the accessory FD, bridge forwarding to `127.0.0.1:9000`) — phone ↔ box.
4. **Log drain** (box-clock semantics, restamp at the push boundary) — box → phone → backend.

### Fresh-clone autonomy (hard requirement)

Every repo, cloned alone, with the standard toolchain: builds green, `git status` clean, prepo unknown to the cloner. Nothing prepo-related is committed anywhere — filters, attributes, and hooks are per-clone local state that `git clone` does not transfer, so a fresh clone is born with none of it. CI is the no-prepo user — it is a fresh lone clone by construction. The structural backstop remains: a `file:` ref or out-of-repo path source that somehow reached a commit cannot resolve in a fresh clone, so CI fails loudly; the prepo-injected guards exist so that never happens on a pushed branch.

## Change set

1. Extraction proceeds per the boundary table; dead trees (`zed/`, `packages/generated/csharp/zed-client/`) are deleted at cutover, not moved.
2. Docs: `AGENTS.md` environment-notes mount list; each side's agent doc references the four contract homes.
3. Pulsar sandbox entries for the new repos (bind mounts at `/<repo-name>/`). Post-discovery (prepo thread) the VSCode pane needs no workspace-template entries for them.

## Discarded alternatives

- **Vendoring `common`/`core` into the zed repo**: duplicates the capture-tar wire-contract types (`CaptureSessionManifest` and friends); drift there is a broken inter-repo contract, not a compile error.

## Open parameters

- Names: both new repos; GHCR image namespaces.
- Phone↔box compat policy (N-1 vs. paired versions; field upgrade ordering); authoritative homes for the four cross-repo contracts.
- Release orchestration across repos (independent cadences vs. coordinated train).
- Git history strategy for the extractions (filter-repo preserving tag ledgers vs. fresh starts); `capture-tool-v*` ledger continuity.
- Dispositions: `rathole-client`, `apps/AndroidMobile`, the licensing pass (Stereolabs base image, vendored OkHttp) for the standalone repos.
