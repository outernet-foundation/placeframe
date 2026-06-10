---
updated: 2026-06-10
---

# Make `uv run build` reuse ghcr layer cache and whole images instead of rebuilding everything locally

## Goal

Local `uv run build` recomputes every target's layers from scratch — including the multi-GB CUDA/torch layers in `localizer`/`reconstructor` — even though CI has already pushed those layers (and sometimes whole images) to ghcr. Make local builds pull/reuse what already exists so a dev who changed only one service doesn't rebuild the whole stack. This directly attacks the make-it-sing local-loop pain (edit `api`, then wait on `localizer`/`reconstructor` rebuilds that didn't change).

This initiative is scoped but **not yet implemented** — we'll implement it later.

## State (verified this session)

What ghcr currently holds (probed via `docker buildx imagetools inspect`):
- **CI layer cache: populated.** `build-cache:api`, `build-cache:localizer-cuda`, `build-cache:reconstructor-cuda` all EXIST. CI pushes a `mode=max` (all-layers) registry cache for every target.
- **Whole `tree-<sha>` images: absent for the current working tree.** This branch (`fix/various-fixes`) has local commits CI never built, so content-hashes don't match any CI-produced image. (They'd be present on a tree that matches a CI build.)

What `uv run build` does today (`build/src/build_scripts/placeframe/build_docker.py`):
- `mode == "ci"`: appends both `cache-to` and `cache-from` `type=registry,ref=build-cache:<target>` per target (push + pull layers). Cache logic gated at the `if mode == "ci":` block (~line 239).
- `mode == "local"`: configures **neither** `cache-to` nor `cache-from` — only the local BuildKit cache is used. So local builds ignore the populated ghcr layer cache entirely.
- `build` always bakes **all** targets; it never checks whether a `tree-<sha>` image already exists.
- Note: `uv run up --pull missing` *does* pull existing `tree-<sha>` images — but `build` never does.

## Decisions

The architecturally-correct shape is **both** improvements (do both; `build` becomes "pull what exists, build only what changed, import shared layer cache for the parts that must build"):

- **A. Import the registry layer cache in local builds — reliable, unconditional win.** Add `cache-from=type=registry,ref=build-cache:<target>` to the local path too, but **not** `cache-to` (dev machines shouldn't push to the shared cache and may lack write perms). A local build of a changed service then pulls its unchanged base/apt/torch/uv-sync layers as cache hits, rebuilding only layers downstream of the edit. Cache confirmed present, so this helps unconditionally — directly kills the recomputed-CUDA-layers cost.
- **B. Skip-or-pull whole images by tree-tag — situational win that compounds with the make-it-sing loop.** Before baking, per target: if `<image>:tree-<sha>` is present locally → skip; else if in ghcr → `docker pull` and drop from the bake list; else → build. Result: build only the services whose content actually changed, pull the rest. No-op on a heavily-diverged branch (like the current one), large win once the branch's services match `dev`/`main` builds.

## Open questions

- **Does `cache-from` cover the `neural-networks-base` layers?** `localizer`/`reconstructor` pull `neural-networks-base` via `additional_contexts: target:…`, and that base target is untagged, so CI likely never cached it independently. Verify empirically; if it's a gap, also cache the `neural-networks-base-*` targets so the heavy base layers are covered.
- Implementation must be validated by confirming the cache actually shortcuts a real CUDA build before claiming it works (don't just trust the flag is present).

## Key files

- `build/src/build_scripts/placeframe/build_docker.py` — the `run_build` function; cache wiring is the `if mode == "ci":` block (~line 239) that needs a local-mode `cache-from` addition, and a new pre-bake existence-check that partitions targets into pull-vs-build. `_get_remote_digest` (~line 59, uses `docker buildx imagetools inspect`) is the existing ghcr-probe helper to reuse for the tree-tag existence check.
- `compose.bake.yml` — defines targets, `tree-<sha>` image tags, and `x-registry-cache: ghcr.io/outernet-foundation/placeframe/build-cache`. `additional_contexts: target:neural-networks-base` is the untagged-base concern for question 1.

## Pending threads

- Implement A and B in `build_docker.py`: add `cache-from` (registry layer cache) to the local path, plus a pre-bake registry/local existence check that partitions targets into pull-vs-build. Then verify a CUDA build is genuinely shortcut by the cache, and check whether `neural-networks-base` layers need their own cache entries.
