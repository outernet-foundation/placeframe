---
updated: 2026-05-24
---

# DIR replacement — opportunistic upgrade

## Goal

Replace the in-tree DIR (Deep Image Retrieval, AP-GeM) implementation
with a modern image-retrieval model when retrieval becomes a
bottleneck. The current setup works and is license-clean (MIT) but is
dated and self-vendored — `packages/python/neural-networks/` carries
the DIR codebase directly rather than depending on an upstream.

This is research-and-prototype work, not a scheduled initiative.

## State

Not started. DIR is in production and not currently the bottleneck.
The retrieval-quality knob has not been the limiting factor in the
end-to-end localization metrics; reconstruction quality and feature
matching dominate.

## Decisions

- **Trigger condition: re-evaluate when retrieval becomes a
  bottleneck.** Define "bottleneck" as: top-K retrieval misses the
  correct map for queries whose features otherwise would have matched
  — measurable from existing localization metrics by partitioning
  failures by stage.
- **Bundle with a planned calibration refit if pursued.** Any DIR
  change shifts the global feature distribution and requires a
  `pipeline_version` bump + calibration refit. Pursuing it solo
  spends a refit cycle on retrieval alone; bundling it with another
  refit-driving change amortizes the cost.
- **Square-tile aggregation composes with any successor unchanged.**
  The current aggregation step downstream of the per-tile retrieval
  is agnostic to the underlying retrieval model, so a swap is local
  to the model-loading + per-tile inference path.

## Open questions

- **Candidate shortlist.** EigenPlaces, SALAD, and DINOv2 + GeM
  pooling all outperform AP-GeM on standard benchmarks. License
  posture, weight availability, and runtime-cost-per-tile need
  comparing before any prototype. None compared in depth yet.
- **Distribution-shift handling.** A change in the retrieval feature
  distribution may require not just calibration refit but also
  per-map re-indexing. The cost of re-indexing all existing maps is
  unknown.

## Key files

- `packages/python/neural-networks/src/neural_networks/` — current
  DIR implementation lives here, vendored.
- `packages/python/neural-networks/SPEC.md` — model loaders, license
  posture, masking design. Any replacement updates this SPEC.
- `docker/localizer/src/` and `docker/reconstructor/src/` — retrieval
  call sites; expected unchanged at the call boundary if the
  successor follows the same `Tensor → top-K map IDs` interface.

## Pending threads

1. Watch the bottleneck condition. No action until retrieval is the
   limiting factor in localization metrics.
2. When triggered: shortlist comparison (EigenPlaces / SALAD /
   DINOv2 + GeM), benchmark on a representative map set, pick one,
   prototype, bundle with the next planned calibration refit.
