---
updated: 2026-06-14
---

# make-it-sing pins the placeframe stack in three places that drift independently

This memory is about the **`/make-it-sing`** repo (a separate sibling repo at `/make-it-sing`), not `/placeframe`. It happens to be stored here under `/placeframe/.pulsar/memories/` because that was the session's cwd. The user was offered the option to relocate it to make-it-sing and had not answered.

## Goal

Updating make-it-sing to a new placeframe version is too manual: it requires hand-resolving an OCI manifest digest and pasting it in. The user wants either the artifact published somewhere stable to point at, or a change to the pinning scheme, so "update to latest" stops being a multi-step "song and dance."

## State

- **Root problem identified:** make-it-sing references placeframe in three independent places with three pinning schemes and nothing keeps them in sync:
  - `compose.yml:6` — OCI compose artifact pinned by **digest** (`oci://ghcr.io/outernet-foundation/placeframe/placeframe-cuda@sha256:…`).
  - `pyproject.toml:11` — `placeframe-bash` source pinned by **commit SHA** (`[tool.uv.sources]`, `rev = …`).
  - `pyproject.toml:12` — `placeframe-unity` source pinned by the same **commit SHA**.
- The pins are already mutually inconsistent: the `pyproject.toml` rev `c3313124…` is the tip of a placeframe feature branch whose compose artifact was **never published** (not on `dev`), so the source pins and the compose pin reference different placeframe versions.
- During the session the stale compose digest was **already edited**: `compose.yml:6` was changed from `sha256:4c31988501592885cdd0bba3d78186ca4a765d0e229a7bcfa4ab9fd5e436a9c1` to the current `dev` digest `sha256:04d3e8d36af917f05625e0f3b809f8ec0c537b59d0336c4b6b2a6db4827ec170`. This edit was **not committed** (it's a code change; commit separately per repo rules). The `pyproject.toml` revs were left untouched.
- **No release/`main` tag exists** for the compose artifact. The registry has only branch tags (`dev`, `feature-air-gapped`, …) plus ~20 placeframe-commit-SHA tags. So "latest" currently can only mean "tip of placeframe's moving, unreviewed `dev` branch."
- A `bump-placeframe` script was **proposed but not built**. The user had not approved the approach; an AskUserQuestion was raised and the user deflected to ask for elaboration rather than answering, then invoked `/memorize`. So the design decisions below are still open.

## Decisions

- **Architecturally correct fix (proposed, not yet accepted): collapse to one knob + one command.** make-it-sing tracks a single placeframe ref, and a `uv run bump-placeframe` script resolves that ref and rewrites all three references atomically:
  - `uv run bump-placeframe` follows dev tip; `uv run bump-placeframe <sha>` pins a specific placeframe commit.
  - Fits existing setup: make-it-sing already pulls `placeframe-bash` / `placeframe-unity` as dev deps — the right toolkit for such a script — so no new infrastructure.
  - Keeps everything reproducible and git-tracked (digest/SHA still land in the files) while killing manual digest resolution and the three-way drift.

## Open questions

These were raised to the user and remain unanswered:
1. **What should "latest" mean** — freshest on `dev`, or a deliberately blessed release? There's no placeframe release/`main` tag today, only moving `dev` + per-commit SHAs.
2. **Should the two `pyproject.toml` revs move together with the compose pin** (one version everywhere), or be decoupled (e.g. compose tracks dev, source libs stay pinned)?
3. **Where should the fix live** — in make-it-sing (a bump script), or pushed back into placeframe (publish a stable pointer / `latest`-style alias make-it-sing can reference without resolving anything)?
4. **How hands-off** — on-demand command vs. auto-PR bot vs. making the reference non-stale so there's nothing to bump.

## Key files

- `/make-it-sing/compose.yml` — line 6 `include:` pins the OCI compose artifact by digest.
- `/make-it-sing/pyproject.toml` — lines 11-12 `[tool.uv.sources]` pin `placeframe-bash` / `placeframe-unity` by commit SHA.
- `/placeframe/build/src/build_scripts/placeframe/ci/publish_compose.py` — placeframe CI that publishes the compose artifact; lines ~102-108 run `docker compose publish` and push to GHCR under both `placeframe-cuda:<git-sha>` and `placeframe-cuda:<branch-name>` tags.

## Reference: how to resolve a tag's digest by hand (the toil to eliminate)

- List tags in the registry (ghcr auth already in `~/.docker/config.json`): a `curl` against `https://ghcr.io/v2/outernet-foundation/placeframe/placeframe-cuda/tags/list` with a bearer token, or `oras repo tags …`.
- Resolve a tag to its immutable digest:
  `docker buildx imagetools inspect ghcr.io/outernet-foundation/placeframe/placeframe-cuda:dev --format '{{.Manifest.Digest}}'`
  (the `application/vnd.oci.empty.v1+json` warnings are harmless.)
- Tag (`:dev`) is mutable and re-pointed every CI run; digest (`@sha256:…`) is immutable. make-it-sing pins by digest per the repo's "pin everything, no moving refs" rule, which is why the pin goes stale when dev moves.

## Pending threads

- Get the user's answers to the four open questions, then build `uv run bump-placeframe` in make-it-sing (or the alternative they pick).
- Decide whether to also realign the two `pyproject.toml` revs to a published placeframe version (currently they point at an unpublished feature-branch tip).
- Commit the already-made `compose.yml` digest bump in `/make-it-sing` (separate code commit), if keeping it.
- Optionally relocate this memory into the make-it-sing repo if that's where the user wants it.
