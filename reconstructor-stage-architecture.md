---
updated: 2026-11-25
---

# Reconstructor stage architecture ADR

Decomposition of the reconstructor's pipeline into per-stage modules behind a thin orchestrator. This ADR rides the `job-lifecycle` branch on top of the landed lifecycle work and builds on its substrate; the lifecycle ADR (`reconstruction-job-lifecycle.md`, repo root) is cited below by settled-design number.

## Status and session protocol

1. **Framing session (complete, 2026-11-25).** Frame identified, settled designs recorded, open questions enumerated under the question bar.
2. **Question-resolution sessions (this is the next thing to do).** Work through the Open questions in listed order, one at a time. Never use the question tool — the operator rules in conversation. A question is closed only when its ruling has been folded back into this ADR (as a settled design or a closed-question record) and committed as its own prose commit; only then does the next question open. A session may close as many questions as the operator has rulings for. If a ruling contradicts an existing settled design, amend that design in the same commit.
3. **Lock.** When no open questions remain, the ADR is locked and this section records the date.
4. **Planning session.** A separate session turns the locked ADR into a linear execution plan (the pattern of `reconstruction-job-lifecycle-plan.md`). From then on the plan sequences work; this ADR stops being load-bearing.

**The question bar.** The architecturally correct thing is always done, regardless of implementation difficulty or blast radius. A question is open only while either the architecturally correct design or the desired behavior is genuinely ambiguous; difficulty and blast radius are never reasons to keep one open, and a question closes when one of the two becomes clear.

**Session mechanics.** Repo root `/workspace/placeframe`, branch `job-lifecycle`; verify a clean tree before edits; prose commits only while questions are open (this file, and agent docs only if a ruling demands it); never push — the operator pushes; never use the question tool.

## Problem

`run_reconstruction()` (`workloads/reconstructor/src/reconstructor/run_reconstruction.py:141–520`) is one ~380-line function holding job setup, capture ingest, feature-shard rehydration, the extraction shard loop, pair generation, both training stages, matching, verification-shard staging, COLMAP dispatch, and post-SfM upload and finalization. `colmap.py`'s `run_colmap_reconstruction` similarly spans two phases. Three structural defects:

1. **The orchestrator knows every stage's durable format.** The feature-shard download loop (rr 226–268) and the verification-shard download loop (rr 465–474) live in the orchestrator, alongside imports of `fetch_valid_shard_indexes`, `get_object_bytes`, and the h5 shard file names. The boundary between job-level sequencing and stage-internal state is smeared: the orchestrator can rebuild every stage's outputs from S3, which is working knowledge no orchestrator should hold.
2. **Model ownership is centralized.** `load_models()` loads all three torch models into module globals in the orchestrator's file, so no stage module is self-sufficient and no future worker could run a subset of stages.
3. **The pipeline cannot be read as a state machine.** Four of six phase transitions sit in the orchestrator, two inside `colmap.py`, and the mapping from code to the `reconstruction_status` enum requires reading two 400+-line functions.

Beyond readability, the fan-out direction (below) requires exactly the boundary this refactor draws.

## Direction: stage-local execution, S3 as the contract

The lifecycle branch already built most of the distribution substrate, mostly via the resume design:

- Markers are a distributed-safe completion record: per-shard, prefix-addressed, idempotent (deterministic stages produce identical bytes; PUTs are idempotent; the marker is written last), validated by `options_hash` + `pipeline_version`.
- Every stage's inputs are already S3-reconstructible on the resume path — with one exception, open question 2.
- The lease law needs zero changes for fan-out. The lease-holder becomes the coordinator: it owns heartbeat, fencing echo, and result reporting; sub-workers are anonymous S3 writers that never touch the row. Late or zombie sub-worker PUTs are already accepted noise (lifecycle settled design 3), and double-dispatch of a shard self-heals — same inputs, same bytes, idempotent PUT, marker last.
- A distributed stage worker and a resumed worker are the same thing: materialize inputs from S3, compute one unit, write it with a marker. The resume code is the proof the slow path works.

```
orchestrator (lease holder): phases, seed, sequencing, drain, result routing
   |
   +-- prepare -> extraction -> pairs -> opq -> pq -> matching -> verification -> sfm
          each stage: compute + shard upload + own rehydration + own models
   v
S3: reconstructions/<id>/  final artifacts + shards/ markers = the only cross-stage contract
```

What stays co-located: the COLMAP chain (database build, verification, SfM share local-disk scratch). What is not built: dispatch machinery (settled design 8).

## Settled design

### 1. One stage module per pipeline stage

**Decision: the package gains one module per pipeline stage plus a `job_context.py`; `run_reconstruction.py` becomes the orchestrator only.** The user-stated shape — orchestrator creates/threads progress, calls each stage's entry function — is architecturally sound: the stage list mirrors the state machine's phase family, and each module becomes independently readable and testable. Stage-to-phase mapping is not 1:1 at two edges (pair generation runs under `EXTRACTING_FEATURES`; SfM artifact emission runs under `RECONSTRUCTING`); those are stage boundaries without phase boundaries and are recorded as such.

| Module | Phase published | Content (moved from) |
|---|---|---|
| `run_reconstruction.py` | — | orchestrator: `JobContext` assembly, phase calls, sequencing, seed, drain, routing |
| `job_context.py` | — | the `JobContext` frozen dataclass |
| `prepare.py` | — (grant-time `EXTRACTING`) | tar download/extract, manifest, `Rig` build, keyframe pre-pass, `OptionsBuilder` (rr 148–208) |
| `feature_extraction.py` | `EXTRACTING_FEATURES` | feature-shard rehydration + shard loop + consolidated `global_descriptors.h5`; ALIKED/DIR models, `n_limit`, `_write_canonical_image` (rr 210–332, 523–529) |
| `pair_generation.py` | (still `EXTRACTING`) | stage entry over pure `pairs.py` + the two pair-file uploads (rr 334–344) |
| `opq_training.py` | `TRAINING_OPQ_MATRIX` | descriptor vstack, load-or-train, stage marker (rr 346–371) |
| `pq_training.py` | `TRAINING_PRODUCT_QUANTIZER` | load-or-train, stage marker, encode, `features.h5` (rr 373–401) |
| `matching.py` | `MATCHING_FEATURES` | matcher + match-shard packing/upload, `empty_cache`, LightGlue model (rr 403–461) |
| `verification.py` | `VERIFYING_GEOMETRY` | from `colmap.py`: DB build, `partition_verification_shards`, replay/run shard loop, parity rewrite, VIO EM check, verified-metrics call, verification-shard rehydration (colmap 89–181 + helpers) |
| `sfm.py` | `RECONSTRUCTING` | from `colmap.py`: `incremental_mapping` + progress callbacks, best-model pick, gravity/first-frame alignment, Umeyama diagnostic, text/npz writers, artifact emission (colmap 183–289) |

Pure libraries stay pure: `pairs.py`, `rig.py`, `keyframes.py`, `options_builder.py`, `metrics_builder.py`, `shards.py`, `uploader.py`, `progress_publisher.py`. Stage entry functions are verb-named module-level functions taking `(context, upstream results)` and returning small frozen dataclasses (`PreparedCapture`, `Features`, `Compression`, `VerifiedGeometry`). `MetricsBuilder` is threaded explicitly as the cross-stage accumulator. `run_reconstruction.py` keeps its name and signature — `main.py`'s import site is stable.

### 2. Stages own their rehydration

**Decision: each stage materializes its own inputs from its own markers when upstream in-RAM state is absent, and the orchestrator imports no shard-read machinery.** This is the boundary correction: today's rehydration loops move out of the orchestrator into `feature_extraction.py` and `verification.py`; the OPQ/PQ load-or-train logic already is stage-local. The post-refactor invariant: `run_reconstruction.py`'s import surface contains stage entry points, `JobContext`, the publisher/uploader types, the status enum, and `MetricsBuilder` — no `shards.py` read machinery, no model globals. This is also the property the distributed direction needs: the resume path is the distributed path, so the component that can resume can also be dispatched.

### 3. Stage-owned models

**Decision: extraction owns ALIKED/DIR and the `n_limit` per-job mutation; matching owns LightGlue; boot-time loading is preserved by per-stage load functions called from `main()`.** Each stage module derives its own `DEVICE` constant. Self-sufficiency beats DRY for a one-line expression: a worker that runs only matching loads only matching, which is the precondition for any future stage-level fan-out. Warm-start behavior is unchanged — the loaders still run at process boot from the same call site.

### 4. `JobContext` in its own module

**Decision: a frozen dataclass `JobContext` carries `reconstruction_id`, `capture_session_id`, `options`, `options_hash`, `pipeline_version`, `s3_client`, `captures_bucket`, `reconstructions_bucket`, `work_dir`, `publisher`, `uploader` — in `job_context.py`, not in `run_reconstruction.py`.** Stages importing the type from the orchestrator's file would be a genuine circular import: the orchestrator imports stage entry functions, stages import the context type back. The context is the job-scoped handle every stage receives; `publisher` and `uploader` ride it as job-scoped services. Publisher construction stays in `main.py` — the granted `lease_attempt` lives there.

### 5. The orchestrator owns the job, not the stages

**Decision: the orchestrator owns `JobContext` assembly, stage sequencing and result threading, phase transitions (five of six — open question 1 for the sixth), stage-boundary lease-loss checkpoints (`set_phase` raises; the explicit raise after SfM returns), the deterministic seed, the final drain, unsuccessful routing, and metrics finalization.** The seed is orchestrator-owned because it seeds the job's process-global RNG (numpy global state + `set_random_seed`), which is cross-stage state. Result reporting (`succeed`/`fail`/`error`/`preempt`), the heartbeat task, and the SIGTERM path stay in `main.worker_loop` — that split is already right. Stages own: compute, shard uploads and markers (their own prefixes and marker extras), rehydration, in-stage `on_progress`, in-loop `raise_if_lease_lost`, their models, and GPU hygiene at their tail (`empty_cache` at matching's end).

### 6. `RECONSTRUCTING` is lifted; `VERIFYING` is the open question

**Decision: the `RECONSTRUCTING` transition moves into the orchestrator, with its total taken from the verification result (`image_count` = `len(colmap_image_ids)`); the flip moment is preserved exactly because today's call (colmap.py:187) sits at the verification/SfM seam, after parity, the VIO check, and the verified-matches metrics — i.e., exactly where `verify_geometry` returns.** `VERIFYING_GEOMETRY`'s ownership is open question 1, because its total (shard count) exists only after the DB build and its current flip happens after the DB build.

### 7. `sfm.py` owns SfM artifact emission

**Decision: the `sfm_model/` upload sweep and the `database.db` upload move into the `sfm` stage, preserving the uploader-queue ordering that makes `database.db` presence imply SfM ran to completion.** The orchestrator keeps only the drain and the unsuccessful routing around it.

### 8. No dispatch machinery

**Decision: the refactor draws the boundary; it does not build fan-out.** No task transport, no worker addressing, no pool lifecycle, no partial-failure aggregation. Mechanism for the wait: carrying cost with nothing to run it on — the gpu-orchestrator's world is one GPU slot under contention, no fleet exists, and the matcher would need a `placeframe_core` restructure before per-machine batches mean anything. The boundary alone makes the later change additive: a stage call becomes "dispatch and await markers" inside the existing seam, with zero lease-server changes (the lifecycle law already tolerates anonymous shard writers, double-dispatch self-healing, and zombie PUTs).

### 9. Behavior-preservation ledger

**Decision: the refactor is behavior-preserving, with exactly these enumerated deltas.**

- Preserved: uploader ordering (`database.db` last); the unsuccessful-path shape pending open question 3; DB-build status timing pending open question 1; the rehydrate-before-compute skip structure inside every shard loop.
- Accepted cosmetic delta: `set_phase(EXTRACTING_FEATURES, total=...))` fires before shard rehydration instead of after it. The row's status value is identical (the grant already set `EXTRACTING`); only `PhaseTimings` attribution of rehydration seconds shifts, and phase timings are diagnostics (lifecycle ADR's metrics stance).
- Churn: `test_verification_shards.py` imports move from `reconstructor.colmap` to `reconstructor.verification`; `main.py`'s `load_models` becomes the two per-stage loaders; `worker_loop` is untouched.

### 10. Minor placements

`@inference_mode()` decorates the two torch-touching stages (`extract_features`, `match_features`) individually. The vstack'd `descriptor_array` is built in `opq_training`'s entry and threaded to `pq_training` (training owns its input assembly; `Features` carries only per-image dicts). `WORK_DIR` stays the fixed single-job path — the single-process, single-job constraint is unchanged and documented.

## The orchestrator, after

`JobContext` is assembled inline at the top (settled design 4); imports elided. Every phase call the orchestrator owns is visible in one function, which is the point:

```python
@inference_mode()
def run_reconstruction(
    capture_id: UUID,
    reconstruction_options: ReconstructionOptions,
    publisher: ReconstructionPublisher,
    uploader: ArtifactUploader,
) -> ReconstructionMetrics:
    context = <JobContext assembly>

    prepared = prepare_capture(context)

    if reconstruction_options.deterministic_seed is not None:
        random.seed(reconstruction_options.deterministic_seed)  # noqa: NPY002 — pycolmap reads numpy's global random state
        set_random_seed(reconstruction_options.deterministic_seed)

    publisher.set_phase(ReconstructionStatus.EXTRACTING_FEATURES, total=len(prepared.image_list))
    features = extract_features(context, prepared)
    pairs = generate_pairs(context, prepared, features)

    publisher.set_phase(ReconstructionStatus.TRAINING_OPQ_MATRIX)
    compression = train_opq_matrix(context, features)

    publisher.set_phase(ReconstructionStatus.TRAINING_PRODUCT_QUANTIZER)
    train_product_quantizer(context, features, compression)

    publisher.set_phase(ReconstructionStatus.MATCHING_FEATURES, total=len(pairs))
    matches = match_features(context, features, pairs)

    metrics_builder = MetricsBuilder()
    verified = verify_geometry(context, prepared, features, pairs, matches, metrics_builder)

    publisher.set_phase(ReconstructionStatus.RECONSTRUCTING, total=verified.image_count)
    reconstruction = reconstruct(context, prepared, verified, metrics_builder)

    publisher.raise_if_lease_lost()

    uploader.drain()
    if reconstruction is None:
        print("Reconstruction failed, no model was created")
        metrics_builder.metrics.successful = False
        return metrics_builder.metrics

    publisher.finalize_timings()
    metrics_builder.metrics.phase_timings = publisher.phase_timings
    metrics_builder.metrics.pipeline_version = context.pipeline_version
    metrics_builder.metrics.successful = True
    return metrics_builder.metrics
```

`verify_geometry` contains today's internal `set_phase(VERIFYING_GEOMETRY, total=shard_count)` after the DB build — pending open question 1.

## Open questions

Work these in order, one at a time, per the session protocol. Each is open because the architecturally correct design or the desired behavior is genuinely unclear.

### 1. Who flips `VERIFYING_GEOMETRY`, and what does DB-build time bill to?

Today `run_colmap_reconstruction` builds the COLMAP database (cameras, images, keypoints, priors, rig config) before `publisher.set_phase(VERIFYING_GEOMETRY, ...)` (colmap.py:144), so DB-build time is spent under `matching_features` in the row's status and in `PhaseTimings`. The status column is the row's lease authority (lifecycle ADR), so this is a state-machine decision, not a style one. `queue-state` counts `in_flight` identically either way; the observable difference is the status label during DB build and phase-timing attribution.

Is the current late flip intended semantics — the row honestly reports the last completed stage's status while a stage assembles its inputs — or an artifact of where the call sat? The worlds: (a) the orchestrator owns all six transitions, one place to read the whole phase map, and the row reads `verifying_geometry` during DB build (a row-visible timing change the refactor would have to own); (b) verification owns its flip, behavior is preserved exactly, and the rule becomes "the orchestrator owns a transition when its total is knowable from prior stage results at the same moment the flip happens today."

### 2. Are match shards the resume record for verification, or does matching recompute?

Every checkpointed stage's outputs double as its resume record, except matching. Match shards are complete — `matches.npz` carries per-pair index slices (`match_a`/`match_b` + `match_offsets`; `pairs.json` the names), exactly what `write_match_rows` consumes — but a resumed run re-executes the whole matcher and rebuilds `match_indices` in RAM, because the matcher runs whole under one descriptor transfer and the parity rewrite consumes full in-RAM match state. The markers currently dedupe only the uploads.

Consequence today: a preemption during verification re-pays the entire matching GPU pass, contradicting the lifecycle ADR's cost model — "an error-routed attempt or a preemption costs the stages after the last marker" (its settled design 10). This is also the one handoff where settled design 2's stage contract cannot hold: verification cannot materialize its match inputs from durable state.

The worlds: (a) match shards become the record. When all match shards are valid, the matcher skips entirely and verification materializes match state from the shards (the parity rewrite reads the materialized state); partial validity still runs the matcher whole and uploads only unmarked shards. The stage contract becomes uniform, and this is precisely the mechanism a distributed verification stage consumes, so the boundary stops misrepresenting the future. (b) Recompute stays the design, one code path, and the deviation is recorded as a sanctioned exception with its reason (the matcher is whole-stage by construction). Note (a) does not require the deferred deep change (per-batch matcher driving in `placeframe_core`) — it is a full-skip path plus a reader. Descriptors still rehydrate from feature shards on every resume for encode, regardless.

### 3. What does a completed-but-unsuccessful run report?

The no-model path returns `metrics.successful = False` and nothing else — no `finalize_timings()`, so no `phase_timings` and no `pipeline_version` (run_reconstruction.py:498–502). The plan that built it says only "fail with the partial metrics," which never defined partial. Is the omission intended (a failed run's timings are not interesting) or an oversight (an operator diagnosing a FAILED job wants to know where time went)? The refactor must know which shape to preserve; if the ruling is "include them," the fix may ride the refactor's scope as its one sanctioned behavior change, or land as its own commit — the ruling should say which.

### 4. How is the orchestrator/stage boundary enforced?

The invariant is settled (settled design 2's import surface, mechanically checked — an import surface is deterministic logic that belongs in code, not review; unenforced invariants rot, and a later session will "just quickly" fetch a shard in the orchestrator). The line is already subtle — `compute_options_hash` legitimately comes from `uploader.py` for `JobContext` assembly. The open part is the mechanism and the exact allowlist: a unit test asserting the module's import surface (repo-idiomatic, lives beside the other reconstructor tests, zero new dependencies) versus import-linter as a dev dependency (declarative contract, but one new workspace-wide dependency for one rule). The ruling names the mechanism and the allowlist it asserts.

## Deliberately deferred (not open)

- **Per-batch matcher driving** — restructuring `make_local_feature_matcher_for_arrays` in `placeframe_core` so match batches can run per machine. Reopen when a real multi-GPU matching fan-out is built.
- **Cross-machine `deterministic_seed` derivation** — per-stage seeds derived from the job seed. Reopen with actual distribution; today the seed is process-global and the worker is single-process.
- **Verification fan-out via per-shard COLMAP DB assembly** — cameras/images/keypoints for a shard's frame pairs plus match rows from shards, final parity DB assembled at the end. The verification/sfm split keeps the door open; the design is not worked.
- **Dispatch transport, worker addressing, pool lifecycle** — no fleet exists; the gpu-orchestrator arbitrates one GPU slot.
- **Marker-gating `features.h5` to skip encode on resume** — encode is CPU-cheap next to the matcher; a micro-optimization.

## Consequences

- The refactor lands as one code commit (module moves, `JobContext`, test import updates) and one prose commit (the `workloads/reconstructor/AGENTS.md` layout tree, the phase-ownership rule, and the boundary rule). No wire, schema, or score change, so no codegen commits; `uv run --locked scripts/preflight.py` before claiming CI-clean.
- `main.py`'s `worker_loop`, result routing, heartbeat, and SIGTERM path are untouched. The API, lease-server, and capture-tool repo are untouched.
- The lifecycle ADR and its plan keep their recorded fates (the operator's decision); this ADR cites them by settled-design number and both remain at the repo root.
- A future distributed verification (open question 2 plus the deferred fan-out) rides this boundary with zero lease-server changes — the lifecycle law already tolerates anonymous shard writers, and this ADR's stage contract is the same contract a dispatched worker satisfies.
