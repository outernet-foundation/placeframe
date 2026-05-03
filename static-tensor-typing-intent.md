# Static Tensor Shape Typing — Intent

> Execution and progress tracked in [`plan.md`](plan.md).
> Companion design intents:
> - VPS redesign: [`vps-redesign-intent.md`](vps-redesign-intent.md).
> - Feature pipeline modernization: [`feature-pipeline-intent.md`](feature-pipeline-intent.md).

## Status

Important but orthogonal — no specific phasing dependency on the VPS calibration arc. Pursued opportunistically when bandwidth allows; the localizer-scope prototype is sufficient until the wider migration is prioritized.

A localizer-scope prototype landed alongside Phase 2c-fixup. What's in place:

- `core/tensor_types.py` — the `TT[*Shape]` torch shim (the only thing in this file).
- Dim brands live next to the concepts that define them: `NumImages` / `MaxTiles` / `NumQueryTiles` in `core/image_preprocess.py`; `RetrievalDim` / `NumKeypoints` / `LocalDescDim` in `core/model_wrappers.py`; `NumMatches` in `core/lightglue.py`.
- `docker/localizer/src/torch_ops.py` — thin per-rank torch wrappers (`from_numpy`, `to`, `stack`, `permute`, `transpose`, `matmul`, `amax`) typed via `@overload` so output shape flows from runtime args.
- `core/numpy_ops.py` — numpy sibling (`zeros` per rank, rank-1 `nonzero` / `compress`).
- `core/model_wrappers.py` — four `make_*` factories returning typed callables: `make_global_descriptor_extractor` (DIR), `make_local_feature_extractor` (ALIKED), `make_local_feature_matcher_for_{tensors,arrays}` (LightGlue). Consumed by both `localize.py` and `run_reconstruction.py`'s `load_models()`.
- `core/lightglue.py` migrated off `NDArray`; exports `Keypoints` / `Descriptors` / `KeypointsArrays` / `DescriptorsArrays` `NewType` brands so positional swaps at the matcher are caught statically.
- 13 remaining `NDArray` imports across the codebase carry `# noqa: TID251 — Phase T piece 3 follow-up migration` to keep lint clean while the wider migration waits.

Wrappers live in `core` (not `neural_networks.models`) because `neural_networks` deliberately doesn't depend on `core` (Docker-build constraint). The `make_*` helpers take `Any` for the raw model; the typed callable they return recovers full brand info at the seam.

The prototype produced disproportionate readability and correctness wins for the size of the diff. Static dim mismatches at function/assignment boundaries are now caught at type-check time without runtime overhead, no library dependency, and no migration off the existing tooling.

## Context

### What this initiative is

Move the codebase from "numpy/torch tensors annotated with dtype only" to "numpy/torch tensors annotated with shape via PEP 646 + NumPy 2.1+ generics," repo-wide. Catch dim-mismatch bugs at type-check time at the boundaries we already type — function signatures, dataclass fields, variable annotations.

### Why this needs to change

- **Tensor-heavy code is currently un-checkable.** Every `NDArray[float32]`, every `Tensor`, every dict-of-arrays surfaces as a shape-erased blob. Reshape arithmetic, axis ordering, and broadcasting bugs land at runtime — sometimes silently, often far from the line that introduced them.
- **Comments documenting shapes drift.** A `# (num_images, max_tiles, descriptor_dim)` comment next to an `NDArray[float32]` declaration becomes a lie the moment the field is reordered. Pyright doesn't read comments.
- **The next several VPS phases (2d masking, 3 calibration) introduce more tensor flow.** Adding shape typing now means the new code lands typed, instead of paying retroactive migration cost again.
- **The tooling exists today and is free.** NumPy 2.1 (Aug 2024) finalized `np.ndarray`'s shape parameter; pyright + mypy 1.7+ have solid PEP 646 support. No new dependency, no runtime overhead, no library bet.

### Design goals (priority order)

1. **Catch dim-mismatch bugs statically** at function/assignment boundaries throughout the localizer, reconstructor, and shared `core` / `neural-networks` packages.
2. **Eliminate `NDArray` and `ndarray[Any, dtype[T]]`** from project source code — every numpy array carries a shape.
3. **Eliminate `Tensor` (untyped torch) where shape is known**, replaced with `TT[*Shape]` or wrapped in a `torch_ops.py`-style operation that flows dim names through.
4. **No `# noqa: TID251`, no `cast(Tensor, ...)` to dodge the type system.** If a boundary is genuinely untypable (third-party return values, neural net outputs), wrap it in a typed helper at the seam — once — and let the rest of the codebase consume the typed result.
5. **Verify the prototype actually works end-to-end** before doing the wide migration. The localizer-scope prototype passed type-check; it has not been exercised against a full reconstruction + localization pipeline.

### Design non-goals

- **Runtime shape checking** (jaxtyping / phantom-tensors). Out of scope. Static checking at boundaries plus the natural runtime errors torch / numpy throw on mismatched shapes are sufficient.
- **Per-element shape arithmetic** (e.g. `reshape` propagating literal sizes through computed dims). Not expressible in Python's type system today; not worth pursuing.
- **Adopting a tensor library** (jaxtyping, phantom-tensors, etc.). Bare NumPy 2.1 generics + a ~17-line `tensor_types.py` shim cover the use case without taking a dependency on a small or unmaintained project.
- **Typing every numpy/torch operation** at the primitive level. The `torch_ops.py` pattern grows opportunistically — a wrapper is added when an operation erases dim names that we want to preserve. Operations that already type correctly through stubs need no wrapping.
- **Ruff custom rules to forbid `ndarray[tuple[int, int], ...]`** (rank-known, sizes-unknown). Legitimate escape hatch for dicts-of-arrays where each entry has a different `N`. `TID251` on `NDArray` plus `reportExplicitAny` cover ~95% of the value with no false positives.

## The pieces

### 1. End-to-end verification of the localizer-scope prototype

The prototype landed under tight scope (the retrieval block in `localize.py` plus `Map.tile_descriptors`). Type-check passes. The runtime correctness of the refactor — particularly the `global_descriptor_extractor` wrapper (replacing the prior `dir` global) in `localize.py` and `run_reconstruction.py`, and the retrieval-block matmul rearrangement (now expressed as `torch_ops.transpose` + `torch_ops.matmul` + `torch_ops.permute`) — has not been confirmed against a full reconstruction + localization run.

- Run an end-to-end smoke against the post-prototype pipeline. After Phase 3 chunk 7 lands, this means `uv run tune-reconstruction --captures <id>` (formerly `test-placeframe-e2e`; renamed) or `uv run fit-calibration --captures <id> --pipeline-version <sha>`. Confirm reconstruction completes; confirm localization produces a non-degenerate pose against a ZED-built map.
- If the scripts aren't ready yet, do the smoke manually: full `uv run up`, build a small test map via the Capture Tool, query it from the Capture Tool with a different camera, verify the returned pose is sane.
- Block widening the migration until this passes.

### 2. Move shared types to `core` and complete the localizer-scope coverage

The prototype already moved `tensor_types.py` to `packages/python/core/src/core/`. Completion items inside the localizer / reconstructor scope:

- `Map.keypoints` and `Map.pq_codes` (currently `dict[int, NDArray[...]]`) typed with rank-correct shapes — `ndarray[tuple[NumKeypoints, Literal[2]], dtype[float32]]` etc. `NumKeypoints` is a per-image brand acknowledging that each entry has its own count; the rank and last-axis size are still meaningful constraints.
- ~~`aliked_output` typed via a Protocol or TypedDict (the analog of the `global_descriptor_extractor` wrapper, but for ALIKED's keypoint/descriptor output).~~ Done — `local_feature_extractor` wrapper returns the typed tuple.
- ~~`lightglue_match_tensors` signature carries shape brands for keypoints / descriptors / match indices.~~ Done — `local_feature_matcher` wrapper + `MatchIndices` type alias in `core/lightglue.py`.
- All `axis_convention.py` functions (translations, rotations, quaternions) typed with `ndarray[tuple[Literal[3]], ...]` etc. Fixed-shape; clean migration.

### 3. Repo-wide migration of `NDArray` usages

Thirteen files import `NDArray` (per Ruff `TID251` enumeration). Migrate each:

- `docker/zed-capture/src/zed/zed_wrapper.py` — translation/orientation/image data; small fixed shapes.
- `docker/reconstructor/src/reconstructor/{run_reconstruction,rig,colmap,metrics_builder}.py` — covered alongside the localizer migration; many shared types.
- `docker/localizer/src/{map,build_metrics}.py` — covered by piece 2.
- `packages/python/core/src/core/{axis_convention,h5,opq}.py` — covered by piece 2 + h5 / opq specifics. (`core/lightglue.py` was already migrated off `NDArray` in the prototype.)
- `packages/python/neural-networks/src/neural_networks/models.py` — DIR / ALIKED preprocessing arrays.
- `scripts/src/scripts/{tune_reconstruction,fit_calibration}.py` (formerly `run_e2e.py`; renamed in Phase 3 chunk 7) — PB-sweep tabulation arrays and the calibration fit's feature/covariance arrays; small fixed shapes.

End state: zero `from numpy.typing import NDArray` imports outside generated code (`packages/generated/` is `.dockerignore`-allowlisted for ruff exclusion already). Zero `# noqa: TID251`.

### 4. Repo-wide migration of bare `Tensor` to `TT[*Shape]` where shape is known

Same pattern as piece 3 but for torch. Less mechanical because torch's stubs don't propagate dim names through operations; each transformation requires a `torch_ops.py`-style wrapper. Grow the wrapper module opportunistically as migration touches each file.

End state: `Tensor` (un-shaped) survives only at boundaries with un-typable third-party calls (neural net outputs, pycolmap returns, etc.) — and even there, the boundary is wrapped in a typed helper that consumes `Tensor` and produces `TT[*Shape]` once.

### 5. Tighten lint enforcement

Once piece 3 + 4 land:

- `TID251` `numpy.typing.NDArray` ban remains.
- Add `reportExplicitAny` to `basedpyright` config to catch new `cast(Tensor, ...)` / `Any` escape hatches that bypass the typed seams.
- Add a `flake8-tidy-imports` ban on bare `torch.Tensor` in domain modules (allow only in `torch_ops.py` wrappers and at neural-net boundaries). Implementation: file-scoped allowlist via `per-file-ignores`.

## Sequencing

1. **End-to-end verification of the prototype.** Blocks everything else.
2. **Piece 2 — localizer / reconstructor full coverage.** Done before widening to other services because the brand vocabulary (`NumKeypoints`, `LocalDescDim`, `NumCorrespondences`, etc.) gets defined here and other services consume it.
3. **Piece 3 — repo-wide `NDArray` migration.** Mechanical, file-by-file. Can be split across multiple commits; each file is independent.
4. **Piece 4 — repo-wide `Tensor` migration.** More judgment-heavy. Grow `torch_ops.py` (or per-service equivalents) as needed.
5. **Piece 5 — lint tightening.** Last, once the migrations are clean.

## Pipeline-version interaction

This initiative does not change the localizer's runtime behavior — it's pure type annotations, casts (no-op), and one wrapper-function refactor (`global_descriptor_extractor` returning a flattened tensor instead of a dict-with-batch-dim, replacing the previous `dir` global). The wrapper change is functionally identical to the prior pattern: same input, same output, same numerical computation. The localizer's git SHA bumps, so `pipeline_version` invalidates calibration — bundle wider migration work alongside any other pipeline change to avoid an isolated calibration refit cost.

## Failure modes

| Condition | Behavior |
|---|---|
| End-to-end smoke fails after the prototype refactor | Investigate root cause. The `global_descriptor_extractor` wrapper (replacing the prior `dir` global) and the retrieval-block matmul rearrangement are the most likely suspects; both are mechanical translations of the prior code and bisecting against the prior commit (`403d9fd1`, "Add square-tile retrieval aggregation") will isolate the regression. Block widening migration until resolved. |
| A piece-3 file resists clean migration (per-entry-different `N` in a dict-of-arrays) | Type with rank-correct shape (`ndarray[tuple[NumKeypoints, ...], ...]`) and accept that literal size doesn't propagate. The cost of an escape hatch here is bounded; the rank + named axes still document intent. |
| A torch operation in piece 4 has no clean wrapper signature (e.g. variadic broadcasting that genuinely depends on runtime shape) | Wrap at the next-higher domain boundary instead of the primitive. If even that fails, document the boundary in `torch_ops.py` with a one-line comment explaining what type information is being deliberately surrendered. |
| New `NDArray` import slips past CI | `TID251` is enforced via Ruff; CI lint catches it. The ban exists exactly to prevent regression. |

## Risks and unknowns

- **Migration is large** (~50+ usage sites across 13 files for piece 3 alone). Risk of bundling too much into one commit and producing unreviewable diffs. Mitigation: per-file commits with a clear common pattern; reviewer-friendly grouping by module.
- **PEP 646 limits** (no per-element bounds on `TypeVarTuple`) force per-rank `@overload` sets (e.g. one `from_numpy` overload per supported rank, six `permute` overloads for 3D's permutations) instead of a single fully-variadic definition. As we touch new ranks during migration, the wrapper module grows. Manageable; just verbose.
- **Pyright's PEP 646 support has rough edges.** Some advanced unifications (variadic middle dims with literal endpoints) work in pyright but not mypy. We're a pyright-only shop in basedpyright strict mode, so this is fine — but worth noting if anyone tries to adopt jaxtyping later.
- **One residual `reportUnknownVariableType` on `from torch import from_numpy`** — torch's stub declares `from_numpy(ndarray) -> Tensor` with no parameter annotation, which pyright treats as Unknown. Our `from_numpy_3d` wrapper consumes it and returns a fully-typed `TT[A, B, C]`, so the unknown does not propagate to consumers; the error is contained to the import line in `torch_ops.py`. Workspace venv now syncs with the `cpu` extra (`uv sync --all-packages --extra cpu`) so torch is resolvable locally and other previously-noisy `reportUnknown*` errors no longer drown out real signal.

## Open tunables

| Parameter | Default | Where used |
|---|---|---|
| Per-rank `to_device_*` arity | 3D today (only one current call site) | `torch_ops.py` |
| Dim brand granularity (e.g. one `NumKeypoints` brand vs. distinct query-side / database-side brands) | One shared brand per concept | brand-defining module per concept (`image_preprocess.py`, `model_wrappers.py`, `lightglue.py`) |
| `reportExplicitAny` enablement | Off currently; on after piece 5 | `pyrightconfig.json` / `pyproject.toml` |
