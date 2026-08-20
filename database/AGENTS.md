# Database

SQL schema files for PostgreSQL. Migrations are applied by the `database-manager` service at startup (see top-level `CLAUDE.md` for the migration command).

The schema files in this directory are the source of truth — `uv run generate-datamodels` introspects the live database and produces the SQLAlchemy + Pydantic types in `packages/generated/python/datamodels/`. Don't hand-edit the generated files.

## `localization_evaluations` cache table

`24_localization_evaluations.sql` defines the cache that `fit_calibration.py` writes during corpus assembly and reads during the fit. Localizing a held-out frame against a reconstruction is deterministic given the keyed inputs *plus* `pipeline_version` (the localizer's git SHA, baked into its image — see `docker/localizer/AGENTS.md` "Determinism"), so persisting evaluation outcomes lets re-fits skip the localization pass.

### Key

5-tuple unique constraint:

| Column | Type | Notes |
|---|---|---|
| `reconstruction_id` | uuid | FK to `reconstructions` |
| `frame_timestamp` | bigint | Unix milliseconds, matching `frames.csv` |
| `retrieval_top_k` | integer | localizer parameter |
| `ransac_threshold` | double precision | localizer parameter |
| `pipeline_version` | text | localizer's git SHA |

`pipeline_version` is in the unique key so localizer code changes accumulate rows alongside historical data rather than overwriting it. Old non-deterministic rows (from before the seed contract that pins per-call torch + pycolmap RNG) live under their own `pipeline_version` and aren't pooled with new ones.

### Value columns

- Localizer outputs: `inlier_ratio`, `reproj_error_median`, `num_inliers`, `num_correspondences`, `num_matches`, `inlier_coverage`, `query_image_diagonal_px`.
- `pnp_covariance double precision[]` — 6×6 (stored as 2-D array; `array_length(arr, 1) = 6 AND array_length(arr, 2) = 6`).
- Truth-error labels: `err_t_m`, `err_r_deg`, `se3_residual double precision[]` (length 6).
- `succeeded boolean`.

CHECK constraints enforce **labels-iff-succeeded**: `succeeded = (err_t_m IS NOT NULL) AND succeeded = (err_r_deg IS NOT NULL) AND succeeded = (se3_residual IS NOT NULL) AND succeeded = (pnp_covariance IS NOT NULL)`. Plus array-length CHECKs on `se3_residual` (=6) and `pnp_covariance` (6×6) when present.

Typed arrays rather than `jsonb` here because every field has a fixed shape and Postgres has no reason to treat the payload as opaque. The schema's general policy (see "Use typed columns by default" below) is that `jsonb` is reserved for opaque, version-evolving payloads; that doesn't apply to these fixed-shape numeric fields.

## Use typed columns by default

Default to typed columns (including typed arrays) for any field with a stable shape the database might reasonably read into. Reach for `jsonb` only when the column carries an opaque, version-evolving payload that the database has no reason to query into — for example, a manifest blob whose shape lives in repo-side Pydantic classes and changes across releases. When you do, pair it with a `*_version smallint NOT NULL` column so older rows remain readable after the shape changes, and document the rationale at the column declaration. Don't reach for `jsonb` as a shortcut to skip schema design.

### Upsert semantics

`POST /reconstructions/{id}/localization-evaluations` upserts via `INSERT ... ON CONFLICT ON CONSTRAINT localization_evaluations_cache_key DO UPDATE`. Second write with the same key is a refresh, not a conflict — cache-table semantics. The `pipeline_version`-in-key invariant protects against silent overwrites from committed code changes; uncommitted iteration is on the operator. The `id` column is reused across upserts.

The constraint is named so the router can reference it by name rather than redeclaring the 5-tuple in Python — single source of truth lives in this SQL file.

### RLS and indexes

Tenant-only RLS; **no orchestrator bypass**. The 5-tuple unique constraint serves `WHERE reconstruction_id = ?` queries as a prefix scan, so **no supplementary indexes** are added. Resist the urge to add a separate index on `reconstruction_id` — the unique constraint covers it.

## sqlacodegen ARRAY type binding

sqlacodegen renders array columns as `mapped_column(ARRAY(Double(...)))`, but this trips basedpyright `reportUnknownArgumentType`: `ARRAY[_T]`'s element type can't be inferred from a `_TypeEngineArgument[_T]` whose inner is itself a generic-without-binding.

The custom generator in `build/src/build_scripts/placeframe/sqlacodegen_generator.py` intercepts `ARRAY` columns in `render_column_type()` and emits `ARRAY[<python_type>](<inner>)` — pyright back-infers the inner type from `ARRAY`'s `_T`. One narrow `cast(TypeEngine[Any], coltype.item_type)` at the seam (item_type is itself typed `TypeEngine[Unknown]`); generated file ships clean. No suppressions added.

If a future migration adds another typed-array column, the generator handles it automatically.
