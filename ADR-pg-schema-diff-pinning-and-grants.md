# ADR: pg-schema-diff upgrade, true pinning, and schema-dir grants

Status: Accepted. The operator interview is complete; every open question
is resolved and the rulings are recorded in "Resolved — operator interview"
below. Execution script (exact files, commands, commit boundaries):
PLAN-pg-schema-diff-pinning-and-grants.md, beside this file.

## Context

A reported bug: the generated C# client's `LocalizationMapCreate` constructor
orders parameters `(Guid reconstructionId, double rotationY, double positionX,
…)` — `rotationY` wedged in second, ahead of the position components
(`packages/generated/csharp/api-client/src/PlaceframeApiClient/Model/LocalizationMapCreate.cs`).

Causal chain, verified end to end:

1. `workloads/database-migrator/entrypoint.sh` runs `pg-schema-diff apply`
   without `--data-pack-new-tables=false`. That flag defaults to true:
   new tables get their columns re-arranged by descending storage size
   (`attlen`) to minimize row padding (`pkg/diff/transform_diff.go`,
   `dataPackNewTables`, upstream). The sort is Go's *unstable* `sort.Slice`,
   so columns of equal size (all doubles, all timestamptzs, all bigints tie
   at 8 bytes) land in a deterministic-but-arbitrary intra-group order.
   Result: the physical `localization_maps` table has `rotation_y` at
   attnum 4, and the authored column order in
   `database/22_localization_maps.sql` never reaches the database.
   Reproduced deterministically on two fresh scratch databases.
2. `generate_datamodels` reflects the live DB; SQLAlchemy iterates columns
   in attnum order (`scripts/src/scripts/generate_datamodels.py`, the
   `sa_inspect(table).mapper.local_table.columns` loop). Pydantic DTO fields
   inherit the scrambled order (`public_dtos.py`).
3. Litestar dumps OpenAPI `properties` in field-declaration order
   (`workloads/api/openapi.json`, `LocalizationMapCreate`).
4. openapi-generator's C# template emits the constructor with required
   properties in schema property order.

Impact: JSON is keyed by name, so the wire format and Python clients are
unaffected. The hazard is C# source level — positional constructor arguments.

Two aggravating facts surfaced during diagnosis:

- Version skew: the migrator image pins `PGS_VERSION=v1.0.2`
  (`workloads/database-migrator/Dockerfile`) while `scripts/preflight.py`
  installs `pg-schema-diff@latest` (resolves to v1.0.9). Same input tree,
  two tools, two plans.
- The intra-group column permutation differs between pg-schema-diff versions
  (v1.0.2-era output ends `…active, lighting`; v1.0.9 output ends
  `…lighting, active`). Any version bump can silently permute DTO field
  order → OpenAPI properties → every generated client signature.

Separately, an upgrade evaluation of v1.0.9 (latest stable, released
2026-08-06) found:

- CLI surface unchanged since v1.0.2 (same flags, same hazard names; only a
  new `dump` subcommand). Today's preflight already runs v1.0.9 against a
  fresh database successfully.
- v1.0.6–v1.0.8 fix three SQL-injection classes (enum labels, policy role
  names / function names, search_path shadowing in bigint→timestamp
  migrations). Exploitability in our single-tenant self-hosted role model is
  low, but they are published CVE-class fixes.
- v1.0.3 raises the Go toolchain floor to 1.25.5. `GOLANG_IMAGE` is
  digest-pinned at `golang:1.22-alpine` (`boatyard.yml`), which cannot build
  v1.0.9 (with GOTOOLCHAIN=auto it would silently download a floating
  toolchain mid-build, defeating the pin).
- v1.0.5 adds unconditional table-privilege diffing. Our grants are applied
  out of band by database-manager (`ALTER DEFAULT PRIVILEGES` under
  `SET ROLE owner` in `configure_database.template.sql`), so every table the
  migrator creates is born with api_user/orchestration_user ACLs that
  `database/*.sql` does not declare. Empirically verified: re-running the
  migrator (v1.0.9) against an already-migrated, granted database plans 69
  REVOKE statements stripping every app grant, then aborts at the hazard
  gate (AUTHZ_UPDATE not allowed; exit 1; nothing applied). This is not
  limited to legacy databases — any persisted-volume stack hits it on the
  second `boatyard up`, because the first up itself creates the granted
  state.

Operator premises accepted during discussion: the data-packing row-padding
win is not worth the ordering damage, and no database on the machines this
work runs on is worth preserving. The wipe is per-machine by construction —
the only volume-destroying path anywhere is an explicit `boatyard down
--volumes` (`boatyard/src/boatyard/verbs/down.py`; nothing shipped wipes
volumes) — so other developers' stacks keep their data and converge on
their next `up`; see decision 8 and the legacy-convergence gate in the plan.

## Decisions

1. **Disable data packing.** Pass `--data-pack-new-tables=false` in
   `workloads/database-migrator/entrypoint.sh`. Authored SQL order becomes
   the single source of column-order truth through the whole chain (physical
   table → psql/pg_dump → SQLAlchemy models → Pydantic DTOs → OpenAPI → C#
   constructors). Preflight inherits the flag automatically (it invokes this
   entrypoint).

2. **Standardize on pg-schema-diff v1.0.9** everywhere; retire v1.0.2.

3. **True pinning, one artifact.** In the migrator Dockerfile, replace
   `go install …@v1.0.2` with a committed tools module
   (`go.mod` + `go.sum`); `go install` from that directory verifies the
   `h1:` SHA-256 module digests — Go's native content pin. Bumping = `go
   get` + committed go.sum diff. In `scripts/preflight.py`, delete the
   `go install …@latest` + GOPATH plumbing entirely and run the migration
   path as containers against localhost:55432: the migrator *image* and,
   per the interview amendment, the database-manager *image* too — until
   now preflight ran database-manager from host source, the same class of
   deviation minus the version skew, so its image packaging was never
   CI-exercised. Preflight already builds the whole postgres-provisioner
   image closure via `boatyard build --targets postgres`. One artifact,
   one pin, CI exercises exactly what ships, no host-run migration-path
   code remains, and the host Go prerequisite for CI disappears.

4. **Bump `GOLANG_IMAGE`** in `boatyard.yml` to a digest-pinned
   `golang:1.25-alpine` and regenerate the boatyard lock. Required by
   decision 2; keeps the build-toolchain pin honest.

5. **Move table grants into the schema dir.** New lexically-last
   `database/99_permissions.sql` holding the `GRANT … ON ALL TABLES IN
   SCHEMA …` statements (api_user DML + orchestration_user SELECT/UPDATE on
   public; auth_user full + api_user read-only on auth). Mechanics, each
   load-bearing:
   - Must use the `ON ALL TABLES` idiom, not `ALTER DEFAULT PRIVILEGES`:
     pg-schema-diff does not track default ACLs at all, so default-privilege
     statements in the to-dir apply only to its shadow temp database and
     silently never reach live. The `99_` prefix sorts after every table
     file, so the grants re-materialize as tracked per-table ACLs in the
     shadow DB on every run and cover future tables automatically.
   - The existing table-side `ALTER DEFAULT PRIVILEGES` block in
     `configure_database.template.sql` is deleted, not moved.
   - `GRANT ON ALL SEQUENCES` lines are deleted outright: the schema has
     zero sequences (uuid PKs via `gen_random_uuid()`).
   - Role names are hardcoded as `placeframe_*` in the schema dir. Accepted:
     the `database/` tree is already placeframe-specific.
   - Ordering constraint (database-manager before migrator) remains, now for
     a visible reason: roles are cluster-wide and must exist before the
     shadow-DB GRANTs resolve.

6. **What stays in database-manager** — exactly the things pg-schema-diff
   structurally cannot see (its world model is schema objects; v1.0.5 added
   *table* privileges only), in two passes around the bootstrap. The
   cluster pass runs before it (`configure_cluster.template.sql`: role
   lifecycle + passwords, `REVOKE ALL ON DATABASE` / `GRANT CONNECT`,
   database ownership transfer — `ALTER DATABASE … OWNER TO`, required
   because the dir's `CREATE SCHEMA` and any future one the migrator
   plans must be creatable as the owner, and `CREATE DATABASE` runs
   before the owner role exists — and extensions, which must install as
   admin because postgis is not a trusted extension). The hardening pass
   runs after it (`harden_schemas.template.sql`: `GRANT USAGE ON SCHEMA`
   and the `EXECUTE ON FUNCTIONS` hardening — schema ACLs and function
   privileges untracked, the same silent-no-op trap as default ACLs).
   The split ordering makes the schema dir the sole creator of schemas:
   its statements stay strict (no idempotent spellings), so a duplicate
   anywhere fails loudly. Everything table/sequence/default-privilege is
   deleted outright. The create op also bootstraps the schema dir into a
   database it just created (decision 7).

7. **Standing hazard gate; creation is bootstrapped, not applied.** A
   hazard class belongs on the standing allow list only if it appears in
   routine evolution (drift-free re-ups and ordinary migrations plan zero
   statements) and its worst case against existing state is acceptable
   unattended. `AUTHZ_UPDATE` — the class covering GRANT/REVOKE, RLS
   enable/disable, and policy changes — fails both tests: it fires
   exactly when authorization changes, which is when a human must look.
   So the migrator never allows it: it runs with
   `HAS_UNTRACKABLE_DEPENDENCIES` alone, unconditionally
   (`stack/score/compose/postgres.yaml`, the k8s rendering, preflight's
   env).    Fresh databases are bootstrapped by database-manager's create op —
   gated on the a priori fact that it just ran `CREATE DATABASE`, never
   on catalog probing — by executing the schema dir directly as the
   owner in one transaction. A crash between database creation and the
   bootstrap transaction fails loudly on the next `up` (the hardening
   pass finds no `auth` schema); the recovery is `boatyard down
   --volumes`, safe because that state can only precede any data.
   This is not an approximation: pg-schema-diff's own shadow build is
   exactly "execute the schema dir as the connection user in a fresh
   database", and against an empty database the apply plan is that DDL,
   so bootstrap-by-SQL and bootstrap-by-apply produce identical states
   without routing pure creation through a hazard gate that exists to
   classify it. The create op runs in three steps — cluster pass,
   bootstrap (iff it created the database), hardening pass — so
   the dir's strict statements execute against a world with no
   pre-created schemas. Adding a table or changing grants against an
   existing database aborts at the gate and requires a per-incident
   override:
   `uv run migrate --allow-hazard AUTHZ_UPDATE` (a `scripts/` verb) runs
   the same migrator image on the stack network with the standing list
   plus the named hazard and with the tool's native y/N prompt on the
   printed plan (`CONFIRM_PROMPT`); the next ordinary `up` is a no-op.
   The override is an argument to a one-off command, never stored state,
   so it cannot rot into standing configuration. Preflight exercises the
   whole choreography: the database-manager image bootstraps, one
   migrator run proves the standing gate passes a no-op plan.
   (An `AUTHZ_UPDATE` allowance *without* decision 5 would execute the
   69 revokes and strip the app's database access — the trap this
   refactor exists to close.)

8. **Recreate and regenerate.** After landing 1–7: recreate the databases
   on the machines where the regen runs (`boatyard down --volumes` —
   per-machine by construction; other developers' stacks are not wiped:
   they converge on their next `up` and keep their scrambled column order
   harmlessly, since SQLAlchemy maps by name and OpenAPI order comes from
   the committed regenerated DTOs). Gated by an empirical
   legacy-convergence check: a legacy granted database under the new
   migrator must converge without stripping app grants (plan step 5).
   Then regenerate datamodels + clients, commit codegen output separately
   with the canonical message `Run generate-clients and
   generate-datamodels`. The regenerated clients reorder constructor
   parameters to authored-SQL order.

## Implementation order

Execution script with exact files, commands, and commit boundaries:
PLAN-pg-schema-diff-pinning-and-grants.md. Summary:

1. Prose commit: interview resolutions + acceptance recorded (lands with
   the plan document).
2. entrypoint flag + tools-module pin + Dockerfile (decisions 1–3).
3. GOLANG_IMAGE bump + boatyard lock regen (decision 4).
4. `99_permissions.sql` + database-manager template fold (decisions 5–6)
   + ALLOWED_HAZARDS (decision 7) + score artifact regen.
5. Preflight switch to running both migration-path images (decision 3,
   amendment).
6. Legacy-convergence gate, then recreate databases (down with volumes,
   up — this machine only), verify column order in pg_catalog (`attnum`
   ordering matches `22_localization_maps.sql`), verify re-up is a no-op
   plan (zero statements, zero hazards), verify grants present
   post-bring-up.
7. Regenerate datamodels + clients; canonical codegen commit (decision 8).
8. Full preflight (`uv run --locked scripts/preflight.py`).
9. Review amendment: conditional hazard gate + `migrate` override verb
   (decision 7 as rewritten; plan's "Review amendments" section).

## Non-goals / explicitly deferred

- **Column-privilege inference in generate-datamodels.** The comment at
  `scripts/src/scripts/generate_datamodels.py` (~line 107) wants the
  read-only skip-list inferred from column privileges instead of hardcoded.
  v1.0.9 does not unblock this: it tracks *table* privileges only
  (`pg_class.relacl`); column ACLs (`pg_attribute.attacl`) are unsupported
  anywhere in the tool. Deferred until upstream adds column-ACL tracking.
  The consumer side will then be nearly free (generate-datamodels already
  connects as `placeframe_api_user`). The comment's wording is refreshed
  on this branch to the versionless fact — pg-schema-diff tracks table
  privileges but not column privileges.
- **K8s override mechanism for the hazard gate.** The standing hazard list
  and the entrypoint's empty/non-empty branch are tier-neutral, but the
  per-incident override verb drives `docker run` against a compose
  network. The k8s equivalent (an attended Job run against the cluster
  DSN) is deferred until the k8s tier needs it.

## Resolved — operator interview

Each question was put to the operator with its recommended default; the
rulings:

1. **Landing shape: one PR.** The pieces are mutually validating and the DB
   recreation collapses all fallout into a single event. Rides the existing
   `adr/pg-schema-diff-pinning-and-grants` branch.
2. **Template consolidation: fold** into one cluster-setup template,
   renamed (`configure_cluster.template.sql`; ~82 lines vs 146 across two
   files today). Roles-before-grants ordering becomes automatic.
3. **Downstream C# consumers: follow-up in the consumer repos**, riding
   each client pin bump; this branch does not touch them. Audit during the
   interview: placeframe-capture-tool has one positional
   `LocalizationMapCreate(...)` call site (`CaptureRow.cs:225`) that is
   provably order-invariant — it passes the identity transform and
   `rotationW` occupies the same slot in both orderings; MapRegistrationTool
   already uses named arguments; make-it-sing has no usage.
4. **Skip-list comment refresh: yes**, with versionless wording — comments
   carry present state, not version history.
5. **Volumes: wipe only where the regen runs.** Nothing shipped wipes
   volumes — the only volume-destroying path is an explicit `boatyard down
   --volumes` (`verbs/down.py`; `up` never tears down, and a destructive
   plan aborts at the hazard gate rather than applying). Other developers'
   stacks converge on their next `up` and keep their data. Legacy
   convergence is verified empirically before landing (plan step 5).
6. **Host Go in CI: deleted with the `go install` path.** It was never
   documented anywhere — an undeclared dependency on the runner image's
   preinstalled Go, load-bearing only because preflight ran the migrator
   entrypoint as a host script. Nothing else in the repo needs host Go;
   there is nothing to remove beyond decision 3 itself.
7. **Amendment — preflight runs both migration-path containers.** Preflight
   also ran database-manager from host source (`uv run --directory
   workloads/database-manager python -m src.main`); no version skew (it
   runs the committed tree) but its image packaging was never
   CI-exercised. Decision 3's preflight rewrite now covers both images.
8. **Review amendment — creation bootstraps; the migrator gates.** The
   migrator runs with the standing hazard list only (`AUTHZ_UPDATE`
   never); fresh databases are bootstrapped by database-manager's create
   op, which owns the emptiness knowledge by construction, executing the
   schema dir directly as the owner; overrides are per-incident attended
   invocations of `uv run migrate --allow-hazard …`, never stored config.
   A hazard that fires only when authorization changes is exactly the
   case that must force a human decision. The cluster template also
   splits around the bootstrap (cluster pass before, schema hardening
   after) so the schema dir remains the sole creator of schemas with
   strict statements.
