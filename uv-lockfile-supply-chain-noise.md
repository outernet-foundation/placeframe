# uv lockfile supply-chain noise — open issue

> Captured 2026-05-02 during chunk 3 of Phase 3. Revisit when astral ships an opt-out, or when the next docker-context dep change forces us back to the wall.

## Symptom

Running `uv run lock-python` (which the [generation pipeline in `CLAUDE.md`](CLAUDE.md) requires after any dep change) regenerates the per-service `docker/<service>/pylock.toml` files (and `docker/neural-networks-base/pylock.neural-networks-*.toml`) with cosmetic-only diffs against the committed versions: every `download.pytorch.org` wheel entry gains an `upload-time = <ISO8601>Z, ` field. URL, hash, version are unchanged. The wheel that gets installed is byte-identical with or without that field.

The diff cascades a full docker rebuild because `pylock.toml` files live in the `.dockerignore` allowlist, and `compute_service_shas` (`build/src/build_scripts/placeframe/context_sha.py:46`) hashes every allowlisted file into each service's `CONTEXT_SHA`. Cosmetic-only change → new SHA → registry pulls fail → local build of every affected image. Wasted hours.

## Root cause

A three-link supply-chain chain, none of which we control:

1. **PyTorch's index added `data-upload-time` HTML attributes** to its simple repository links at some point on or after 2026-04-28 (the date of `dddeca1d`, the last commit whose pylocks lacked these fields). Per PEP 700, the simple repository v1.1 spec lets indexes expose upload timestamps as link attributes. Sample link from `https://download.pytorch.org/whl/cpu/torch/`:

   ```html
   <a href="..." data-upload-time="2026-02-06T16:27:17Z">torch-2.10.0-1-...whl</a>
   ```

2. **uv 0.6.15+ reads and emits `upload-time`** in lockfiles. Added in [astral-sh/uv#12968](https://github.com/astral-sh/uv/pull/12968) (committed 2025-04-21, released as 0.6.15 on 2025-04-22). The format is permitted by [PEP 751](https://peps.python.org/pep-0751/) (the pylock.toml standard) — `upload-time` is an *optional* field.

3. **uv has no opt-out flag.** Verified against `uv export --help`, `uv lock --help`, the changelog, and issue tracker:
   - No `--no-upload-time` / `--exclude-upload-time` / `--minimal-metadata` / `UV_NO_UPLOAD_TIME` / `[tool.uv] include-upload-time = false`.
   - The closest issues go the *opposite* direction: [#15220](https://github.com/astral-sh/uv/issues/15220) wants `uv lock --force` to write the *newest* format (with upload-time). [#13247](https://github.com/astral-sh/uv/issues/13247) reports the `upload-time` → `upload_time` field rename. [renovatebot discussion #35589](https://github.com/renovatebot/renovate/discussions/35589) confirms `revision = 1` (pre-uv-0.6.15) lockfiles lack the field while `revision = 2/3` (uv 0.6.15+) include it.

## Why pinning uv doesn't fix this on its own

Pinning a specific uv version (e.g. via `[tool.uv] required-version = "==X.Y.Z"`) is good hygiene against version drift between developers, CI, and the docker base image. It does **not** fix this issue:

- Any pinned uv ≥ 0.6.15 reads `data-upload-time` from the index and emits it on export. Field will reappear regardless of which exact version is pinned.
- The only pinning that prevents emission is `≤ 0.6.14`. That requires:
  - Updating `compose.bake.yml` `UV_BASE_DIGEST` and `.env.lock` to a docker base image that bundles uv 0.6.14 (`ghcr.io/astral-sh/uv:0.6.14-python3.13-bookworm-slim` exists). One-time rebuild of every python-bundled service image (api, state-sync, database-manager, auth-initializer, gateway, etc.).
  - Forgoing all uv improvements and bug fixes from the past year.
  - Vulnerable to the *next* informational field uv decides to write that we didn't anticipate (this isn't a unique-to-upload-time problem; it's structural).

## Why post-processing the pylock at write time was rejected

We discussed adding a strip step to `_export_pylock` in `build/src/build_scripts/placeframe/lock_python.py` to remove `upload-time = ...,` from the exported file. Rejected on principle: lockfiles are the wrong artifact to post-process. uv should produce a deterministic output and we should commit what it produces.

## What we actually did this turn

**Option 4 (defer):** Skip `uv run lock-python` in chunk 3. The chunk's only dep change (numpy/scipy added to `scripts/pyproject.toml`) lands in a workspace member that has **no Dockerfile**, so per-service `pylock.toml` files don't actually need to change. `uv.lock` (root, outside docker context) gets the dep additions. Per-service pylocks stay byte-identical to origin/dev. Zero docker rebuild. Zero upload-time exposure. Origin/dev's pylock state is preserved untouched.

This works for chunk 3 specifically because of the workspace-member coincidence. It does **not** work for any future change that touches a docker-relevant service's deps. The next such change forces us back to one of:

- Pin uv ≤ 0.6.14 (full rebuild + year-old uv).
- Post-process pylocks in `lock-python` (rejected on principle).
- Absorb the upload-time diff once (rejected this turn).
- Wait for astral to ship an opt-out (no ETA).

## What needs to happen upstream

File a feature request with [astral-sh/uv](https://github.com/astral-sh/uv/issues) asking for one of:

- **Best:** `[tool.uv] include-upload-time = false` (project-level config, deterministic across machines).
- **Acceptable:** `--no-upload-time` flag on `uv export` and `uv lock`, plus `UV_NO_UPLOAD_TIME` env var.
- **Minimum:** Document a supported way to produce a stable, supply-chain-noise-invariant lockfile. Otherwise, pylock.toml is unsuitable for use as a docker build context input — which contradicts the PEP 751 motivation for tool-agnostic reproducible lockfiles.

The framing for the issue: a lockfile's contract is "reproducible installs" — only fields that affect what gets installed should drive lockfile diffs. `upload-time` does not affect resolution, install, or hash verification. Including it without an opt-out makes lockfile content dependent on arbitrary index metadata, breaking the reproducibility-vs-version-control contract.

## When to revisit

- When astral ships an opt-out: pin to that uv version, set the flag, regenerate pylocks. Done.
- When the next docker-context dep change forces a `lock-python` regen: decide between the four options listed above. Re-read this doc first.
- If pytorch.org or any other index adds *another* informational field that uv decides to emit: same wall, same options. The fix is structural, not field-specific.

## Files relevant to this issue

- `build/src/build_scripts/placeframe/lock_python.py` — produces per-service pylocks via `uv export`.
- `build/src/build_scripts/placeframe/context_sha.py` — hashes allowlisted files into per-service CONTEXT_SHA.
- `.dockerignore` — allowlist that includes `docker/`, hence the pylocks.
- `docker/neural-networks-base/pylock.neural-networks-*.toml` — most affected (most pytorch.org wheel entries).
- `docker/api/pylock.toml`, `docker/reconstructor/pylock.toml`, `docker/localizer/pylock.toml`, etc. — also affected when their dep graph touches pytorch.org.
