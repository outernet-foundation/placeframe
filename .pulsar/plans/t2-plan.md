## Implementation Plan: T2 — SHA-based Image References

### Context

Currently, CI builds Docker images, writes their digests to `.env.lock`, and commits that file back to the branch. This creates noisy main-only commits and couples image identity to a post-build artifact rather than the source commit. Since built images are a deterministic function of the commit SHA plus pinned base images, we can tag them with the commit SHA directly and eliminate the `.env.lock` commit step for built images entirely.

### Approach

**Step 1: Update `compose.bake.yml` to accept `GIT_SHA` for tagging**

Each build target currently has a hardcoded `:latest` tag. Add a second tag using `GIT_SHA` so that both are produced. The bake file supports variable interpolation from the environment, so the approach is:

- For each service in `compose.bake.yml`, change the `tags` array from `["ghcr.io/.../service:latest"]` to `["ghcr.io/.../service:latest", "ghcr.io/.../service:${GIT_SHA}"]`.
- `GIT_SHA` will be set in `os.environ` by `build_docker.py` before invoking `docker buildx bake`. Docker Bake resolves `${GIT_SHA}` from shell environment variables in tag strings (confirmed: bake HCL/YAML tag fields support env var interpolation when the variable is in the process environment).
- Keep `:latest` as a secondary tag for backward compatibility during transition and for human convenience. It can be dropped later.

**Step 2: Update `build_docker.py` to compute and inject `GIT_SHA`, stop writing built-image entries to lock files**

In `build/src/build_scripts/placeframe/build_docker.py`:

- At the top of `build()`, compute `git_sha = bash_output("git rev-parse HEAD").strip()` and set `os.environ["GIT_SHA"] = git_sha`. This makes it available to the bake file's tag interpolation.
- Remove the post-bake loop (lines 231-235) that writes `*_IMAGE` entries for baked services into `lock_data`/`local_lock_data`. The baked image digest entries (`API_IMAGE`, `STATE_SYNC_IMAGE`, etc.) should no longer be written to `.env.lock` in CI mode.
- For **local** mode (`mode == "local"`), the `.env.local.lock` still needs built-image entries because locally built images are `--load`ed (not pushed to a registry) and have no SHA tag on GHCR. The local lock should store the image name from metadata (e.g., `ghcr.io/.../api:latest`) as the value for `API_IMAGE` etc. But since compose.yml will now use `${GIT_SHA}` for built images, local mode needs a different override mechanism — see Step 4.
- The `_write_lock_file(LOCK_FILE, ...)` call at line 238 for CI mode should only write base/third-party entries. In CI mode, skip writing `local_lock_data` entirely (the SHA tag on GHCR is the identity).

**Step 3: Update compose files to use `GIT_SHA` for built services**

In `compose.yml`, for every service that appears in `compose.bake.yml` (i.e., built from this repo), change from the `${SERVICE_IMAGE:?err}` pattern to a hardcoded registry path with `${GIT_SHA:?err}` tag:

| Service | Current `image:` | New `image:` |
|---|---|---|
| `initialize-cloudbeaver` | `${INITIALIZE_CLOUDBEAVER_IMAGE:?err}` | `ghcr.io/outernet-foundation/placeframe/cloudbeaver-initializer:${GIT_SHA:?err}` |
| `create-database` | `${CREATE_DATABASE_IMAGE:?err}` | `ghcr.io/outernet-foundation/placeframe/database-manager:${GIT_SHA:?err}` |
| `auth-initializer` | `${AUTH_INITIALIZER_IMAGE:?err}` | `ghcr.io/outernet-foundation/placeframe/auth-initializer:${GIT_SHA:?err}` |
| `gateway` | `${GATEWAY_IMAGE:?err}` | `ghcr.io/outernet-foundation/placeframe/gateway:${GIT_SHA:?err}` |
| `migrate-database` | `${MIGRATE_DATABASE_IMAGE:?err}` | `ghcr.io/outernet-foundation/placeframe/database-migrator:${GIT_SHA:?err}` |
| `api` | `${API_IMAGE:?err}` | `ghcr.io/outernet-foundation/placeframe/api:${GIT_SHA:?err}` |
| `state-sync` | `${STATE_SYNC_IMAGE:?err}` | `ghcr.io/outernet-foundation/placeframe/state-sync:${GIT_SHA:?err}` |

Remove the `x-image-ref` field from these built services (it no longer serves a purpose since the image name is hardcoded).

In `compose.cuda.yml`:
| Service | Current | New |
|---|---|---|
| `reconstructor-cuda` | `${RECONSTRUCTOR_CUDA_IMAGE:?err}` | `ghcr.io/outernet-foundation/placeframe/reconstructor-cuda:${GIT_SHA:?err}` |
| `localizer-cuda` | `${LOCALIZER_CUDA_IMAGE:?err}` | `ghcr.io/outernet-foundation/placeframe/localizer-cuda:${GIT_SHA:?err}` |

In `compose.rocm.yml`:
| Service | Current | New |
|---|---|---|
| `reconstructor-rocm` | `${RECONSTRUCTOR_ROCM_IMAGE:?err}` | `ghcr.io/outernet-foundation/placeframe/reconstructor-rocm:${GIT_SHA:?err}` |
| `localizer-rocm` | `${LOCALIZER_ROCM_IMAGE:?err}` | `ghcr.io/outernet-foundation/placeframe/localizer-rocm:${GIT_SHA:?err}` |

Third-party services (`minio`, `postgres`, `keycloak`, `ngrok`, `cloudbeaver`, `initialize-minio`, `minio-logger`) keep their existing `${SERVICE_IMAGE:?err}` pattern unchanged.

**Important design note on `GIT_SHA` variable passing**: Docker Compose resolves `${GIT_SHA}` from the shell environment, not only from `--env-file`. The `bash_handoff` in `up.py` uses `os.execvpe` which inherits `os.environ`. So setting `os.environ["GIT_SHA"]` before calling `bash_handoff` is sufficient -- no need to put it in an env file. This is the cleanest approach.

**Step 4: Update `up.py` and `down.py` to compute and export `GIT_SHA`**

In `build/src/build_scripts/placeframe/up.py`:

- Import `bash_output` from `common.bash`.
- Before building the compose command, compute `git_sha = bash_output("git rev-parse HEAD").strip()`.
- Set `os.environ["GIT_SHA"] = git_sha`. Since `bash_handoff` uses `os.execvpe` (which inherits `os.environ`), the variable will be available to `docker compose` for substitution.
- For local builds with `.env.local.lock`: The local lock file will now contain `GIT_SHA=<local-sha>` as an override entry (written by `build_docker.py` in local mode). When loaded via `--env-file`, it will override the computed SHA with whatever SHA was active when the local build ran. **Alternatively**, a simpler approach: in local mode, `build_docker.py` tags local images with the SHA too (via `--load`), so the computed HEAD SHA naturally resolves to the right local image. No `.env.local.lock` override of `GIT_SHA` needed — the local build already tagged images with that SHA.
- **Chosen approach for local mode**: `build_docker.py` in local mode already sets `GIT_SHA` in environment before bake, so local images get tagged `service:$GIT_SHA`. When `up.py` computes `GIT_SHA` from `git rev-parse HEAD`, it matches. The `.env.local.lock` no longer needs built-image entries at all — it only needs base/third-party digests (if any were overridden locally). **However**, if the user modifies code after `uv run build` without rebuilding, `HEAD` will have moved and the SHA won't match any local image. To handle this: `up.py` can check if `.env.local.lock` exists and contains a `GIT_SHA` entry, and if so, use that value instead of computing from `git rev-parse HEAD`. This way, `build_docker.py` in local mode writes `GIT_SHA=<sha-at-build-time>` to `.env.local.lock`, and `up.py` picks it up.

Updated `up.py` logic:
```
1. Compute git_sha from git rev-parse HEAD
2. If .env.local.lock exists and not --locked:
   a. Load .env.local.lock
   b. If it contains GIT_SHA, use that value instead (local build override)
3. Set os.environ["GIT_SHA"] = git_sha
4. Construct docker compose command (same --env-file flags for .env and .env.lock/.env.local.lock)
5. bash_handoff(command)
```

In `build/src/build_scripts/placeframe/down.py`: Apply the same `GIT_SHA` computation. `down.py` passes `--env-file` to compose, and compose will error on `${GIT_SHA:?err}` if the variable is missing. Set `os.environ["GIT_SHA"]` the same way (read from `.env.local.lock` if present, else `git rev-parse HEAD`).

**Step 5: Update `build_docker.py` local mode to write `GIT_SHA` to `.env.local.lock`**

In local mode, after bake completes:
- Instead of writing `API_IMAGE=ghcr.io/.../api:latest` etc., write a single `GIT_SHA=<sha>` entry to `.env.local.lock`.
- Continue writing base/third-party digest entries to `.env.local.lock` as before (these override `.env.lock` for any locally re-resolved digests).

**Step 6: Strip built-image entries from `.env.lock`**

Remove all `*_IMAGE` entries for built services from `.env.lock`:
- Remove: `API_IMAGE`, `AUTH_INITIALIZER_IMAGE`, `CREATE_DATABASE_IMAGE`, `GATEWAY_IMAGE`, `INITIALIZE_CLOUDBEAVER_IMAGE`, `MIGRATE_DATABASE_IMAGE`, `STATE_SYNC_IMAGE`, `LOCALIZER_CUDA_IMAGE`, `LOCALIZER_ROCM_IMAGE`, `RECONSTRUCTOR_CUDA_IMAGE`, `RECONSTRUCTOR_ROCM_IMAGE`
- Keep: all `*_DIGEST` entries (base images) and third-party `*_IMAGE` entries (`CLOUDBEAVER_IMAGE`, `INITIALIZE_MINIO_IMAGE`, `KEYCLOAK_IMAGE`, `MINIO_IMAGE`, `MINIO_LOGGER_IMAGE`, `NGROK_IMAGE`, `POSTGRES_IMAGE`)

**Step 7: Update `build_docker.py` to distinguish built vs third-party in lock writes**

The current code at line 161 writes everything to `LOCK_FILE`. After this change, in CI mode, the lock file write should only include base digests and third-party images. The built-image digest loop (lines 231-235) should be removed entirely for CI mode. For local mode, replace it with writing `GIT_SHA` to `.env.local.lock`.

The `third_party_images` dict (line 144-148) already correctly identifies services NOT in `bake_data["services"]`. This distinction is preserved.

**Step 8: Update CI workflow (`.github/workflows/placeframe.yml`)**

- **`build-docker` job**: Remove the "Upload .env.lock" step (lines 110-115). CI no longer needs to upload per-variant lock files since built-image digests are no longer tracked in `.env.lock`.
- **`commit` job**: Remove the "Download env-lock artifacts" step (lines 232-236). Remove the dependency on `build-docker` if no other artifacts flow from it (but keep the dependency for ordering — we want images built before commit). Actually, if `commit_artifacts.py` no longer needs to merge env-locks, its `.env.lock`-related logic is gone.
- **`commit_artifacts.py`**: Remove `_merge_env_locks()` function and its call. Remove `.env.lock` from the `git add` command. The script still commits `build/versions.json` and `package.json` files (from the `publish` job), so it should not be deleted — just simplified.
- **`paths-ignore`**: Remove `.env.lock` from the `paths-ignore` list on both `push` and `pull_request` triggers. Since CI no longer commits to `.env.lock` for built images, the risk of infinite trigger loops is gone. Base/third-party digest updates to `.env.lock` are intentional developer commits that should trigger CI.

**Step 9: Update `ci/build_docker.py` to set `GIT_SHA` in CI environment**

In `build/src/build_scripts/placeframe/ci/build_docker.py`, the `ci_main` function calls `build(...)`. Before that call, compute and set `os.environ["GIT_SHA"]`. In CI, `GITHUB_SHA` is available as an environment variable, so: `os.environ["GIT_SHA"] = os.environ["GITHUB_SHA"]`. This is more reliable than `git rev-parse HEAD` in CI (which may differ if checkout uses a merge ref). Actually, since the workflow checks out `ref: ${{ github.head_ref || github.ref_name }}`, `git rev-parse HEAD` should match. But using `GITHUB_SHA` or computing from git in `build_docker.py` itself is fine — the key point is that `GIT_SHA` must be in `os.environ` before bake runs.

Given that `build_docker.py` (the shared function) is called by both local and CI paths, it is cleanest to compute `GIT_SHA` inside `build_docker.py` itself: `os.environ.setdefault("GIT_SHA", bash_output("git rev-parse HEAD").strip())`. This allows CI to override via env var if needed but defaults to the git HEAD.

### Key files

**Modify:**
- `/placeframe/compose.yml` — Replace `${SERVICE_IMAGE:?err}` with hardcoded `ghcr.io/.../service:${GIT_SHA:?err}` for all 7 built services; remove their `x-image-ref`; keep third-party services unchanged
- `/placeframe/compose.cuda.yml` — Same pattern for `reconstructor-cuda` and `localizer-cuda` (2 services)
- `/placeframe/compose.rocm.yml` — Same pattern for `reconstructor-rocm` and `localizer-rocm` (2 services)
- `/placeframe/compose.bake.yml` — Add `"ghcr.io/.../service:${GIT_SHA}"` as a second tag to every build target's `tags` array
- `/placeframe/build/src/build_scripts/placeframe/build_docker.py` — Compute `GIT_SHA` via `git rev-parse HEAD`, set in `os.environ`; stop writing built-image digests to lock files; in local mode write `GIT_SHA` to `.env.local.lock` instead of per-service image entries
- `/placeframe/build/src/build_scripts/placeframe/up.py` — Compute `GIT_SHA` (or read from `.env.local.lock`), set in `os.environ` before `bash_handoff`
- `/placeframe/build/src/build_scripts/placeframe/down.py` — Same `GIT_SHA` computation as `up.py`
- `/placeframe/build/src/build_scripts/placeframe/ci/build_docker.py` — Optionally set `GIT_SHA` from `GITHUB_SHA` (or rely on `build_docker.py`'s default)
- `/placeframe/build/src/build_scripts/placeframe/ci/commit_artifacts.py` — Remove `_merge_env_locks()` and its call; remove `.env.lock` from `git add` command
- `/placeframe/.github/workflows/placeframe.yml` — Remove env-lock upload/download steps; remove `.env.lock` from `paths-ignore`
- `/placeframe/.env.lock` — Remove all 11 built-service `*_IMAGE` entries; keep 7 third-party `*_IMAGE` entries and 7 `*_DIGEST` entries

### Verification

**Automated/static checks:**
1. Grep `compose.yml`, `compose.cuda.yml`, `compose.rocm.yml` for `\${GIT_SHA:?err}` — confirm all built services use it
2. Grep same files for built-service `*_IMAGE` variable references — confirm none remain
3. Grep `.env.lock` for built-service image entries (`API_IMAGE`, `STATE_SYNC_IMAGE`, etc.) — confirm they are gone
4. Grep `compose.bake.yml` for `GIT_SHA` — confirm it appears in tag arrays
5. Run `uv run ruff check .` and `uv run basedpyright` to confirm no lint/type errors in modified Python
6. Confirm `commit_artifacts.py` no longer references `env-lock` or `.env.lock`
7. Confirm workflow YAML has no `env-lock` artifact upload/download steps

**Manual/integration checks:**
1. Run `GIT_SHA=test docker compose -f compose.yml --env-file .env --env-file .env.lock config` — confirm all image references resolve correctly (built services get `...:test`, third-party get full pinned refs)
2. After CI runs on a branch: `uv run up` pulls SHA-tagged images from GHCR
3. After `uv run build` locally: `uv run up` uses locally-built SHA-tagged images
4. `uv run up` on a commit with no CI-built images fails with a clear error (the `{GIT_SHA:?err}` pattern produces a useful message, plus Docker will error on image-not-found)
