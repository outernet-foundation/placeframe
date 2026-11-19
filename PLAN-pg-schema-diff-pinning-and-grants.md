# Plan: pg-schema-diff upgrade, true pinning, and schema-dir grants

Execution plan for `ADR-pg-schema-diff-pinning-and-grants.md`. The ADR's operator
interview is complete (resolutions below); this document is the execution script
for the implementing session. Do not re-interview.

## Interview resolutions

| # | Question | Resolution |
|---|---|---|
| 1 | Landing shape | One branch/PR carrying decisions 1–7 plus codegen commits |
| 2 | Template consolidation | Fold `configure_database.template.sql` residue into one cluster-setup template, renamed |
| 3 | Downstream C# consumers | Follow-up in consumer repos, riding each client pin bump; only positional call site (`placeframe-capture-tool` `CaptureRow.cs:225`) is provably order-invariant |
| 4 | Skip-list comment | Refresh, versionless wording ("tracks table privileges but not column privileges") |
| 5 | Dev-stack volumes | Wipe only where the regen runs; other devs converge on next `up` and keep data; legacy convergence verified empirically before landing |
| 6 | Host Go in CI | Deleted with the `go install` path; nothing else needs it; no doc mentions exist to remove |
| 7 | Preflight fidelity (amendment) | Preflight runs **both** database-manager and migrator as images; no host-run migration-path code remains |

Branch: `adr/pg-schema-diff-pinning-and-grants` (already carries the ADR
commit `1bbd3f3e`); steps 1–8 ride the same branch — one PR, prose and code
in separate commits. The sandbox cannot push — commit locally and hand the
branch name + HEAD SHA to the operator at the end.

## Steps

Each numbered step ends at a commit boundary. Prose commits (ADR/plan) and code
commits never mix. Codegen commits use their exact canonical messages.

### Step 0 — prose commit (lands with this document)

The ADR is updated in the same commit as this plan: status Proposed →
Accepted, open questions replaced by the resolutions, amendment 7 folded
into decision 3, decision 8 and the premises scoped to per-machine wipe.
Commit message: `Record interview resolutions for pg-schema-diff ADR`.

### Step 1 — flag + tools-module pin + Dockerfile (decisions 1–3)

Files:

- `workloads/database-migrator/entrypoint.sh` — append `--data-pack-new-tables=false`
  to the `args=(apply …)` array. While there, fix the header comment: line 5 says
  `SCHEMA_DIR` but the code reads `DATABASE_SCHEMA_DIR`.
- `workloads/database-migrator/tools/` — new committed Go tools module:
  `go.mod` (module `placeframe/migrator-tools`, `go 1.25` toolchain directive,
  require `github.com/stripe/pg-schema-diff v1.0.9`) + `go.sum` (carries the `h1:`
  module digests — Go's native content pin; produce via `go mod tidy` with Go ≥ 1.25
  on the host or in a `golang:1.25-alpine` container) + `tools.go` with a
  blank import of `github.com/stripe/pg-schema-diff/cmd/pg-schema-diff` behind
  `//go:build tools`.
- `workloads/database-migrator/Dockerfile` — build stage: `COPY
  workloads/database-migrator/tools/ /tools/`, `WORKDIR /tools`, `go install
  github.com/stripe/pg-schema-diff/cmd/pg-schema-diff` (no `@version` — the version
  and digests come from the module). Delete `ARG PGS_VERSION`.

No `.dockerignore` change: the `!workloads/` allowlist entry already covers the
new `tools/` subtree (the allowlist is directory-granular).

Commit: `Disable data packing and pin pg-schema-diff via tools module`.

### Step 2 — GOLANG_IMAGE bump + relock (decision 4)

- `boatyard.yml` line 11: `GOLANG_IMAGE: "docker.io/library/golang:1.25-alpine"`.
- Regenerate the lock: `uv run boatyard lock` from repo root. The lock resolves
  through the org mirror (`ghcr.io/outernet-foundation/mirror/...`); if the mirror
  lacks `golang:1.25-alpine` the lock fails loudly — surface it to the operator
  (mirror population is CI-side) rather than working around it.
- `GOLANG_IMAGE` is a build-stage base image: no compose/k8s artifact carries it,
  so this step does not stale `stack/generated/`.

Commit: `Bump GOLANG_IMAGE to golang:1.25-alpine and relock`.

### Step 3 — grants into schema dir + template fold + hazards (decisions 5–7)

Files:

- `database/99_permissions.sql` — new, lexically last. Exact content:

  ```sql
  -- Table grants as tracked per-table ACLs. ON ALL TABLES, never ALTER DEFAULT
  -- PRIVILEGES: pg-schema-diff tracks table ACLs but not default ACLs, so
  -- default-privilege statements in this directory would apply only to its
  -- shadow database and silently never reach live. The 99_ prefix sorts after
  -- every table file, so these re-materialize as per-table ACLs on every run
  -- and cover future tables. Role names are hardcoded placeframe_* because this
  -- tree is placeframe-specific; the roles are cluster-wide and are created by
  -- database-manager, which runs before the migrator.

  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO placeframe_api_user;
  GRANT SELECT, UPDATE ON ALL TABLES IN SCHEMA public TO placeframe_orchestration_user;
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth TO placeframe_auth_user;
  GRANT SELECT ON ALL TABLES IN SCHEMA auth TO placeframe_api_user;
  ```

  No `GRANT ON ALL SEQUENCES` (the schema has zero sequences — uuid PKs via
  `gen_random_uuid()`), no function grants (function privileges untracked —
  those stay in database-manager).

- `workloads/database-manager/src/sql/` — delete `configure_database.template.sql`
  and `put_roles.template.sql`; create one `configure_cluster.template.sql`
  (~82 lines): the full `put_roles` content (role lifecycle, passwords,
  `REVOKE ALL ON DATABASE` / `GRANT CONNECT`, session bounce) followed by the
  `configure_database` residue (uuid-ossp + postgis extensions, schema ownership,
  `REVOKE … ON SCHEMA FROM PUBLIC`, `GRANT USAGE ON SCHEMA`, function-EXECUTE
  hardening). Everything table/sequence/default-privilege is deleted outright.
  Merged params header covers identifiers, literals, passwords, database,
  auth_schema.
- `workloads/database-manager/src/main.py` — `_put_roles` collapses to a single
  `postgres_cursor(database_name, …)` connection executing
  `configure_cluster.template.sql` once with the merged format params (role
  creation is cluster-wide and runs fine connected to the target database, which
  exists by then; `_create_database` order is unchanged).
- `ALLOWED_HAZARDS` gains `AUTHZ_UPDATE` → value
  `HAS_UNTRACKABLE_DEPENDENCIES,AUTHZ_UPDATE` in three places:
  `stack/score/compose/postgres.yaml:98`, `stack/score/k8s/postgres.yaml:184`,
  `scripts/preflight.py:27`.
- `scripts/src/scripts/generate_datamodels.py:99-101` — replace the comment with
  versionless wording: the skip-list is hardcoded because pg-schema-diff tracks
  table privileges but not column privileges, so column-privilege inference is
  unavailable.

Regenerate score artifacts (the authored env change stales both renderings) —
**from a clean clone, not this dirty tree**, per `stack/AGENTS.md`:

```bash
git clone --branch adr/pg-schema-diff-pinning-and-grants . /tmp/clean
cd /tmp/clean && uv run boatyard generate-score
# copy stack/generated/** back, verify only ALLOWED_HAZARDS lines changed
```

Commits: `Move table grants into the schema dir` (code), then
`Run generate-score` (artifacts).

### Step 4 — preflight runs images (decision 3 second half + amendment 7)

`scripts/preflight.py`: delete the `go env GOPATH` / `go install …@latest` block
(lines 53-57) and the host-run invocations (lines 58-65). Replace with:

- The existing `boatyard build --targets postgres` already builds all three
  images of the postgres provisioner's closure (postgres wrapper,
  database-manager, migrator) — no new build step.
- `docker run` database-manager image, mirroring the compose provisioner's
  invocation (`stack/score/compose/postgres.yaml:71-85`): entrypoint `uv run
  --no-sync python -m src.main --op create --name placeframe` + the four
  `--*-password password` flags, env `POSTGRES_HOST=localhost
  POSTGRES_ADMIN_USER=postgres POSTGRES_ADMIN_PASSWORD=password`, with
  `--network host` so localhost:55432 reaches the throwaway postgres.
- `docker run` migrator image: env `DB_HOST=localhost DB_PORT=55432
  DB_NAME=placeframe DB_USER=placeframe_owner DB_PASSWORD=password
  DATABASE_SCHEMA_DIR=database ALLOWED_HAZARDS=HAS_UNTRACKABLE_DEPENDENCIES,AUTHZ_UPDATE`,
  `--network host`.
- Image refs via `uv run --locked boatyard tree-tags <name>` per image, same
  pattern as the existing postgres tag lookup (verify exact target spelling with
  `--help`).
- Drop now-dead env: `APP_DIR`, `BACKEND`, `DB_*` host plumbing from
  `os.environ.update` (keep `POSTGRES_*` — `generate-datamodels` still consumes
  them).

Sanity-check the rewritten flow manually before committing: `uv run --locked
scripts/preflight.py` should pass end-to-end against the throwaway postgres
(it exercises the same images the stack runs).

Commit: `Run database-manager and migrator images in preflight`.

### Step 5 — legacy-convergence gate (resolution 5, before any wipe)

Scratch verification that a legacy DB (old grants via `ALTER DEFAULT
PRIVILEGES`, no `99_permissions.sql` state) converges safely under the new
migrator:

1. Throwaway postgres on host port 55433 (`pf-legacy-postgres`).
2. database-manager image `--op create` against it (old template state is
   irrelevant — roles are identical in both worlds).
3. Build tables by running the migrator image built from the **pre-branch**
   commit (or `git stash` the schema-dir change and rebuild), i.e. without
   `99_permissions.sql` and without the flag.
4. Apply the legacy grants: render the pre-branch
   `configure_database.template.sql` (from git history) with `placeframe_*`
   names via psql — its table grants + `ALTER DEFAULT PRIVILEGES` blocks.
5. Run the **new** migrator image (branch state) against it. Gate:
   - exit 0;
   - plan contains no REVOKE that strips api_user/auth_user/orchestration_user
     table access (grantor bookkeeping churn is acceptable, app-access strip is
     not);
   - `SELECT has_table_privilege('placeframe_api_user','capture_sessions','SELECT')`
     etc. remain true after.

If the gate fails, stop and surface to the operator — do not proceed to step 6,
do not widen `ALLOWED_HAZARDS` further.

No commit (verification only).

### Step 6 — recreate databases (this machine only)

`uv run boatyard down --volumes` then `uv run boatyard up --quiet-pull`
(timeout 600000 on these calls). This wipes `pf-postgres-data`,
`seaweedfs-data`, `loki-data` **on this machine only** — other machines are
untouched (nothing shipped wipes volumes; verified: the only `-v` in boatyard is
the explicit `down --volumes` flag, `verbs/down.py:18`).

Verify:

- Column order: `docker exec placeframe-pf-postgres-1 psql -U placeframe_owner
  -d placeframe -c "SELECT attnum, attname FROM pg_attribute WHERE attrelid =
  'localization_maps'::regclass AND attnum > 0 ORDER BY attnum;"` — must match
  `database/22_localization_maps.sql` authored order (tenant_id, created_at,
  updated_at, reconstruction_id, position_x … rotation_w, name, lighting,
  active, color, id).
- Re-up no-op: `docker run --rm <migrator image + env as in step 4>` against the
  running stack's postgres (DB_HOST over the compose network or host port) —
  plan must be zero statements, zero hazards.
- Grants present: `has_table_privilege` checks for all four roles on public +
  auth tables.

No commit.

### Step 7 — regenerate datamodels + clients (decision 8)

Order (per root `AGENTS.md`):

1. `uv run generate-datamodels` (postgres is up from step 6)
2. `uv sync --all-packages --extra cuda` then `uv run lock-python`
3. `uv run generate-clients --config openapi-client-codegen.yaml`
   (needs Java ≥ 11: `sudo apt-get install -y default-jre-headless` if missing)

Expect the C# `LocalizationMapCreate` ctor to read `(Guid reconstructionId,
double positionX, …, double rotationY, …, double rotationW, int color)` —
authored-SQL order.

Commit: `Run generate-clients and generate-datamodels`.

### Step 8 — full preflight + handoff

`uv run --locked scripts/preflight.py` from repo root — must be green
(includes lint/type/pytest battery, the rewritten image-based database battery,
datamodel + client staleness gates). Then hand off: report branch name, HEAD SHA,
per-step commit list, and any deviations from this plan to the operator for
push.

## Verification checklist (all must hold before handoff)

- [ ] Step 5 legacy-convergence gate passed (recorded output)
- [ ] attnum order matches authored SQL
- [ ] re-up migrator plans zero statements, zero hazards
- [ ] all four roles' table grants present post-bring-up
- [ ] regenerated clients show authored order
- [ ] full preflight green
- [ ] no host Go anywhere: `rg "go install" scripts/ workloads/` returns only the
      Dockerfile-internal tools-module install

## Deferred (tracked, not in this branch)

- placeframe-capture-tool `CaptureRow.cs:225` → named arguments (consumer repo,
  rides the client pin bump)
- Column-privilege inference in generate-datamodels (blocked upstream; comment
  refreshed this branch)

## Review amendments

Branch review ruled the hazard policy (ADR resolution 8). Steps, each at a
commit boundary:

### R1 — prose

ADR decision 7 in its final form (standing gate + bootstrap), decision 6
extended with the database-ownership transfer, resolution 8 recorded, k8s
override deferred in Non-goals. In the final history all prose (ADR + this
plan) rides the single tip commit.

### R2 — bootstrap in database-manager

- `workloads/database-manager/src/database_utils.py` — transactional cursor
  variant (autocommit off; explicit commit, rollback on exception).
- `workloads/database-manager/src/main.py` — the create op runs in three
  steps: cluster pass (`_put_roles`), bootstrap (only when the op itself
  created the database — the a priori bit from `_database_exists`, no
  catalog probing — executing every `database/*.sql` in lexical order as
  the owner in one transaction), hardening pass (`_harden_schemas`). A
  crash between database creation and the bootstrap transaction fails
  loudly at the hardening pass; recovery is `boatyard down --volumes`,
  safe because that state can only precede any data.
- `workloads/database-manager/src/sql/configure_cluster.template.sql` —
  cluster pass only: roles, database-level grants, extensions, ownership.
  `ALTER DATABASE {database} OWNER TO {owner}` because the dir's
  `CREATE SCHEMA` needs the owner to own the database (and `CREATE
  DATABASE` runs before the owner role exists). No schema creation, no
  schema hardening.
- `workloads/database-manager/src/sql/harden_schemas.template.sql` — new,
  post-bootstrap: schema USAGE and function-EXECUTE hardening, which are
  untracked by pg-schema-diff and must find the schemas the bootstrap
  just created.
- `database/02_schemas.sql` stays strict (`CREATE SCHEMA auth`): the
  schema dir is the sole creator of schemas, so no idempotent spellings.
- `workloads/database-manager/Dockerfile` — `COPY database/ /app/database/`.

Commit: `Bootstrap the schema in database-manager on fresh databases`.

### R3 — standing list + preflight

- `stack/score/compose/postgres.yaml` + `stack/score/k8s/postgres.yaml` —
  `ALLOWED_HAZARDS` stays `HAS_UNTRACKABLE_DEPENDENCIES` (net unchanged
  from dev).
- `scripts/preflight.py` — migrator env carries the standing list; a single
  migrator run after the create image (which bootstrapped) proves the
  standing gate passes a no-op plan.
- No `Run generate-score`: the hazard-env round-trip netted to dev's value,
  so the artifact diff is empty.

Commit: `Run database-manager and migrator images in preflight`.

### R4 — override verb

`scripts/src/scripts/migrate.py`, entry point in `scripts/pyproject.toml`,
and the migrator entrypoint's `CONFIRM_PROMPT` env (omits
`--skip-confirm-prompt` so the tool's y/N prompt on the printed plan is
the consent).
Commit: `Add the migrate verb for hazard overrides`.

### R5 — docs

`database/AGENTS.md` grants paragraph, root `AGENTS.md` preflight
paragraph, `scripts/AGENTS.md` verb row + preflight description,
`workloads/AGENTS.md` database-manager row.
Commit: `Record the grants model and migration-path changes in the agent docs`.

## Execution record

Steps 0–8 all executed and the verification checklist passed in full. Commits,
in order: `433f42c8` (step 1), `ee10d829` (step 2), `7a83ed91` + `5c40a0e6`
(step 3 code + score), `a79b3fd0` (step 4), `014d810e` (step 7 codegen),
`8499893c`→`f01b59da` (post-plan boatyard 0.9.0 bump). Deviations from the
scripted steps:

- Step 4's "no new build step" premise was false: `boatyard build --targets
  postgres` builds exactly the named target, not the provisioner closure
  (nothing expanded it — the old preflight ran the migration path from host
  source and needed no images). Preflight now names all three targets.
- Mid-initiative pivot: the org mirror lacked `golang:1.25-alpine` and only a
  PR's own `mirror-images` job can write the mirror, blocking every local
  migrator build. Resolution: boatyard gained the gitignored values-file key
  `bypass_image_mirror` (lock records upstream spellings; decoration applied at
  consumption; `build` skips it under the key — boatyard 0.9.0), and this
  branch briefly pinned boatyard by path to use it before release. The pivot
  and its net-zero revert ride the branch as `7474ec77` + `fecb76bb`.
- Step 6 ran without a full `boatyard up`: the executing sandbox had no stack
  (no volumes or containers; `down --volumes` was a no-op) and building the
  GPU closure serves no check. All postgres-scoped verifications (attnum
  order, no-op re-up, grant matrix) ran against the new-migrator-built
  throwaway on 55432 instead of a compose stack postgres. Other machines
  converge on their next `up` per the ADR premises.
- Step 4's env pruning widened beyond APP_DIR/BACKEND/DB_*:
  `DATABASE_SCHEMA_DIR` and `ALLOWED_HAZARDS` were equally dead in
  `os.environ.update` and dropped with them.
- Post-plan: boatyard 0.9.0 published; `f01b59da` bumps the floor to
  `>=0.9`, relocks `boatyard.lock.yml` to the upstream-spelled format (pure
  prefix strip, identical digests — CI's `lock --check` demands it), and
  teaches the two score-generation test helpers to decorate lock refs before
  comparing against baked artifacts. `generate-score --check` confirmed zero
  artifact drift.

The legacy-convergence gate's outcome is worth keeping: a legacy database
(alter-default-privileges grants, scrambled columns) under the new migrator
plans *zero* statements — the legacy per-table ACLs are identical to what
`99_permissions.sql` materializes, so nothing revokes and nothing reorders
existing tables; convergence is a pure no-op, with new tables only getting
authored order and tracked grants.

Review amendments R1–R5 executed after branch review ruled the hazard
policy: creation bootstraps in database-manager, the migrator gates with
the standing list only. Full preflight green end-to-end (exit 0): the
database-manager image bootstraps the throwaway (strict schema dir, one
transaction), the hardening pass applies schema usage + function
EXECUTE, one migrator run passes the standing gate as a no-op, and the
datamodel staleness check confirms the bootstrapped column order matches
the committed datamodels. The post-bootstrap privilege matrix was
verified directly (schema USAGE for api/orchestration on public and
auth/api on auth, table grants per `99_permissions.sql`, function
EXECUTE for api_user, database owned by `placeframe_owner`). Two
mechanics surfaced during execution and are folded into the design: the
database needed ownership transferred to the owner role (the schema
dir's `CREATE SCHEMA` requires it, and `CREATE DATABASE` runs before the
owner role exists), and an early `IF NOT EXISTS` patch to
`02_schemas.sql` was rejected in review — the fix is ordering (the
hardening pass runs after the bootstrap) so the schema dir stays the
sole creator of schemas with strict statements. The create op's
emptiness probe was likewise removed on review — bootstrap is gated on
the a priori `created` bit, so a crash between database creation and
bootstrap fails loudly at the hardening pass (recovery: `boatyard down
--volumes`, safe because the state precedes any data) instead of being
silently healed by catalog inference. The branch history was
rebuilt into single-purpose commits (pin, relock, grants, bootstrap,
preflight, verb, codegen, agent docs) with the ADR and this plan as one
droppable prose tip commit; the score artifacts are net-unchanged
against dev, so no `Run generate-score` commit exists.
