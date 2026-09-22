# Observability stock consumption — dissolving the wrapper images

Thread 5, Phase 4 replacement ([program](tooling-consolidation.md), [index](polyrepo.md)). The planned `observability-images` repo is **cancelled before creation** (operator challenge 2026-09-22, "take nothing as gospel"; probe verdict GO). Loki, alloy, and grafana are consumed as digest-pinned **stock mirror images with compose `configs:`**, not as baked wrapper images. This doc is the complete implementation plan — staged, with operator verification gates — written to be executable by a session with no other context.

## Problem

The observability tier is three two-line wrapper images (`FROM mirror/<stock>` + `COPY` config), built per tree-SHA, published to `ghcr.io/outernet-foundation/placeframe/{loki,alloy,grafana}`, and consumed by the server stack (`compose.yml`) and the box (`compose.rig.yml`, images pulled/built by `install-zed`). The wrappers contain zero unique code; the "specialness" is 134 lines of YAML config. The planned Phase 4 would have created a whole repo + CI + publish pipeline + release ceremony to share those two COPY lines across placeframe and the future capture repo.

## Ground truth

**Consumers today:**

- Server: `compose.yml` `initialize-loki` (:320), `loki` (:328), `alloy` (:348), `grafana` (:359) — all `ghcr.io/.../placeframe/<name>:${<NAME>_SHA:?err}`; commands select in-container config paths (`-config.file=/etc/loki/config.yaml -config.expand-env=true`, `run /etc/alloy/config.alloy`).
- Box: `docker/zed-capture/compose.rig.yml` `aoa-loki`/`aoa-alloy` (:66-84) — same wrapper images via `${LOKI_IMAGE:-...:${LOKI_SHA:?err}}`; `install-zed` computes tree-SHAs over `compose.zed.bake.yml`, then pulls from ghcr (default) or cross-builds into a transient host registry (`--build`). Box compose plugin is pinned at 5.1.1 (`DOCKER_DEBS`).
- Make-it-Sing: consumes the whole server stack via `include: oci://ghcr.io/.../placeframe/placeframe-cuda@sha256:...` — references `http://alloy:4317` on the shared network. The bundle is produced by `build/src/build_scripts/placeframe/ci/publish_compose.py`: regex-substitutes internal vars into copies of `compose.yml` + `compose.postgres.yml` + `compose.<variant>.yml` held in a **temp dir**, pins placeframe-namespace image refs to digests, runs `docker compose publish`.
- Configs: `docker/loki/config.yaml` (server: S3 storage, env-expanded creds), `docker/loki/box.yaml` (box: loopback bind, filesystem storage, 1970 epoch floor for the no-RTC boot), `docker/alloy/config.alloy` (one file serves both stacks; `LOKI_WRITE_ENDPOINT` env drives the only difference), `docker/grafana/provisioning/datasources/datasources.yaml`.
- Digests already pinned in `.env.lock`: `LOKI_DIGEST`, `ALLOY_DIGEST`, `GRAFANA_DIGEST` (`@sha256:...` suffix form, consumed as `.../grafana/loki${LOKI_DIGEST:?err}`).

**Probe evidence (2026-09-22, compose v5.1.3, real registry round-trip):**

1. `docker compose publish` (default flavor) emits a **YAML-only** OCI artifact. A relative bind mount declared in an included file resolves against compose's materialization cache (`~/.cache/docker-compose/<hash>/`), where the source file **does not exist**.
2. The failure is silent-bad: `create_host_path` auto-creates an **empty directory** at the source; the container mounts it and fails at runtime (`cat: read error: Is a directory`). No config-time error. A naive bind-mount switch would have broken Make-it-Sing quietly.
3. **Escape hatch verified**: top-level `configs:` with inline `content:` rides the artifact as YAML data and materializes correctly on the include consumer — proven through publish→include→up with the file's content observable in the container.
4. The loki mirror digest is a **manifest list containing arm64** (alloy's likewise — its arm64 wrapper build FROM that digest already proves it). Digest-pinned box pulls resolve natively.
5. **Anonymous pull works** (HTTP 200 with an anonymous token) — the box's credential-less `sudo docker pull` posture carries over unchanged.

## Design

- All three services switch to stock mirror refs: `ghcr.io/outernet-foundation/mirror/docker.io/grafana/<name>${<NAME>_DIGEST:?err}` — identical posture to every other third-party image in the stack.
- Configs ride compose top-level `configs:` with `file:` sources; service-level long syntax mounts them at their **existing in-container paths** (`/etc/loki/config.yaml`, `/etc/loki/box.yaml`, `/etc/alloy/config.alloy`, `/etc/grafana/provisioning/datasources/datasources.yaml`) so the `command:` overrides stay byte-identical. Runtime env expansion (`-config.expand-env=true`, alloy's `env("LOKI_WRITE_ENDPOINT")`) is unaffected.
- The published OCI bundle carries configs as inline `content:` — the rewrite happens in `publish_compose.py`'s bake step (it must: the baked files live in a temp dir where `file:` paths dangle).
- Box: install-zed scps `box.yaml` + `config.alloy` **flat** into `~/.placeframe/` beside `compose.rig.yml`; the rig compose references them as `file: ./box.yaml` / `file: ./config.alloy` (relative to the compose file's dir — correct both on the box and in any scratch-dir render; nothing in-repo runs compose.rig.yml, verified). Loki/alloy are pulled on the box directly from the mirror in **both** install modes (stock images are never built locally).
- `initialize-loki` (chown sidecar) switches to the stock loki ref — it only needs the image's busybox shell.
- What is given up: tag↔config immutability (running config = the file the deployment has; install-zed is the only box-side writer), and the box deployment surface grows by two files. Both accepted by operator ruling 2026-09-22.

## Staged change set

Two stages, each ending in an operator verification gate. Stage A deliberately **keeps the box's wrapper supply chain alive** (zed bake targets, loki/alloy Dockerfiles, loki/alloy targets in `compose.bake.yml` so CI keeps pushing fresh wrapper tags) — dropping them early breaks install-zed in between (`compute_service_shas` stops emitting `LOKI_SHA`/`ALLOY_SHA` → `ZED_SERVICES` KeyErrors; `--build` bakes nonexistent targets).

### Stage A — server half (no install-zed changes)

1. `compose.yml`: the four services (initialize-loki, loki, alloy, grafana) switch to stock mirror refs + `configs:` (file-sourced). Add top-level `configs:` block. Keep commands, healthchecks, env, chown sidecar.
2. `compose.bake.yml`: drop **only** the grafana build target. Loki/alloy targets stay until Stage B.
3. Delete `docker/grafana/Dockerfile` (provisioning tree stays — it becomes the configs source).
4. `publish_compose.py`: after the regex var substitution, round-trip each baked file through YAML and rewrite every top-level `configs.<name>.file` to `content:` (read the file relative to repo root). Dump with `sort_keys=False` and a huge width (no line folding). Add the YAML lib to `build/pyproject.toml` deps if absent (check first; regen locks).
5. `.dockerignore`: remove entries that only cover the deleted grafana Dockerfile. **Do not touch loki/alloy entries** — the wrapper builds still COPY the configs through Stage B.
6. Agent docs (separate prose commit): `docker/AGENTS.md` observability paragraph (also fix its stale "Alloy mounts /var/run/docker.sock" claim — alloy is an OTLP receiver, no docker.sock); `build/AGENTS.md` if the publish-compose description needs the configs-inline note.

Code commits: (a) compose switch + grafana bake drop + Dockerfile deletion + .dockerignore; (b) publish_compose.py rewrite (+ dep). Then the prose commit.

**Verification (agent, before handing to operator):** `docker compose --env-file .env --env-file .env.lock -f compose.yml -f compose.postgres.yml config` shows configs resolved from the right files; `uv run up` smoke — loki/alloy/grafana healthy; full preflight green (sandbox invocation: `env -u UV_PYTHON PATH="$HOME/.local/bin:$PATH" .venv/bin/preflight`, capture exit codes explicitly; it tears down/rebuilds `compose.postgres.yml`).

**Operator gate 1:** push branch, wait green CI (build-docker pushes fresh wrapper tree-SHA tags — the default install path needs them; `--build` needs no CI). Then run `install-zed` on the bench box either mode — **must work exactly as today** (box still gets wrapper loki/alloy). This is a regression check of Stage A only; it exercises none of the new mechanism. Optionally also verify Make-it-Sing against the branch bundle: `include: oci://ghcr.io/outernet-foundation/placeframe/placeframe-cuda:tooling-consolidation` (branch tag exists — publish_compose emits `<sha>` + `<branch>` tags) in a scratch compose, `config` + `up`.

### Stage B — box half (the new mechanism)

7. `compose.zed.bake.yml`: drop loki/alloy targets (their `LOKI_DIGEST`/`ALLOY_DIGEST` arg references vanish with them).
8. `compose.bake.yml`: drop loki/alloy targets.
9. Delete `docker/loki/Dockerfile` + `docker/alloy/Dockerfile`; `box.yaml`, `config.alloy`, `config.yaml` stay in-tree as mount sources.
10. `docker/zed-capture/compose.rig.yml`: aoa-loki/aoa-alloy → `ghcr.io/.../mirror/docker.io/grafana/<name>${<NAME>_DIGEST:?err}` + `configs:` (`file: ./box.yaml`, `file: ./config.alloy`, targets at the existing in-container paths). Rewrite the two stale "wrapper image" comments. Drop the `${LOKI_IMAGE:-...}` override form — the stock ref + digest env is the whole reference.
11. `install-zed` (~40 lines): `constants.py` — `ZED_SERVICES` drops to the three built services; add `ZED_STOCK_IMAGES` (loki/alloy mirror refs, digest env keys) and config source/remote constants (`LOKI_BOX_CONFIG_SOURCE`, `ALLOY_CONFIG_SOURCE`, `REMOTE_LOKI_CONFIG`, `REMOTE_ALLOY_CONFIG`). `orchestrator.py` — parse `LOKI_DIGEST`/`ALLOY_DIGEST` from `.env.lock` (via `docker_devkit.modes.parse_env_file`, already a scripts dep) and pass to `install_box`. `box_install.py` — `_acquire_images` unchanged loops over the three built services plus one pull loop over `ZED_STOCK_IMAGES` (both modes; never built locally); scp the two configs to `~/.placeframe/`; the box `.env` write carries the three SHA keys + images as today **plus** the two digest lines; flip the box_install "configs ride inside the wrapper images" comment. **Zero edits** to any of the historically fragile machinery (SSH bootstrap, DHCP claim, appliance strip, USB device-mode, NVIDIA runtime, systemd, camera daemons, control-master teardown).
12. `.dockerignore`: remove the loki/alloy Dockerfile entries; config entries may also go (nothing COPYs them anymore).
13. Agent docs (prose commit): `scripts/AGENTS.md` — the install-zed entry points table line and the "`install-zed` disables L4T's USB device-mode service" paragraph's image-acquisition tail ("all five" → three built + two stock pulls; delete the "Building loki/alloy here is load-bearing" sentence); `docker/zed-capture/AGENTS.md` box-loki/alloy references.

Code commits: (a) bake drops + Dockerfile deletions + .dockerignore; (b) install-zed + compose.rig.yml. Then the prose commit.

**Verification (agent):** scratch-dir render — copy `compose.rig.yml` + `box.yaml` + `config.alloy` + a stub `.env` (SHA vars, digests, `ZED_BOX_ID`) into a temp dir, `docker compose config` resolves configs and interpolates cleanly; ruff + basedpyright + deptry green via preflight.

**Operator gate 2 (bench):** `install-zed` in both modes. New failure modes are loud: mirror pull failure aborts with `SystemExit`; env/compose mismatch dies at `up` on `:?err` interpolation; no silent half-deploy. Confirm: box stack healthy, box-Loki queryable (`wget -qO- 'http://127.0.0.1:3100/...'` on-box), phone AOA + log drain functional (the drain reads box-Loki through box-Caddy). Rollback is `git revert` of the Stage B commits + re-run (install-zed is idempotent).

### After both gates

- Make-it-Sing repins its include digest at its own cadence (its current pin keeps serving the last wrapper-based bundle until then).
- Stale `placeframe/{loki,alloy,grafana}` tags remain on ghcr (immutable history); deleting the packages is an optional operator cleanup, no consumer references them after Stage B.

## Discarded alternatives

- **`observability-images` repo (original Phase 4)**: discarded 2026-09-22 before creation. A repo + CI + publish pipeline + release ceremony for two COPY lines, when the specialness is config YAML deliverable by the configs mechanism. The original thread-4 audit ruling ("a shared images repo for two COPY lines is overkill") was the surviving position; the ≥2-consumer concern is met by the configs living in each consumer repo (`box.yaml` box-only, `config.yaml` server-only, `config.alloy` a one-file mirror with its existing third-consumer revisit trigger).
- **Naive stock + bind mounts**: killed by probe facts 1-2 — the OCI bundle is YAML-only and relative binds silently become empty directories on include consumers. Only viable with the `content:` inline mechanism (fact 3).
- **Keep the wrappers**: preserves tag↔config immutability, but costs a shared repo (or duplicated wrappers), a CI publish round-trip per config tweak, and stays the odd one out against the stack's all-stock-digest posture.

## Open parameters

- Cold-session reads before editing: `.dockerignore` (entry shapes for `docker/loki|alloy|grafana` — a repo-wide grep found no direct name hits, so coverage is via broader patterns; prune only what becomes stale, keep loki/alloy alive through Stage A); `build/src/build_scripts/placeframe/ci/preflight.py` image-ref checks (confirm stock mirror refs pass its policy; adapt the check only if it hardcodes wrapper expectations); `build/src/build_scripts/placeframe/ci/build_docker.py` + `.github/workflows/placeframe-ci.yml` (confirm the docker build job bakes whole files, no hardcoded per-target lists); `build/pyproject.toml` (YAML lib presence).
- Box compose plugin 5.1.1 vs probe's 5.1.3 — same major; `configs: file:` is stable spec surface; bench-verified at gate 2.
- Grafana stock ref is amd64-only — fine, server-only service.
