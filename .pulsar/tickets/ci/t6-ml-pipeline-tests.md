---
id: T6
title: Integration tests for reconstruction and localization pipelines
status: blocked
depends_on:
  - T5
---

# T6: Integration tests for reconstruction and localization pipelines

See `ci-background.md` for shared CI context.

## Goal

End-to-end tests that verify the reconstruction and localization pipelines produce correct results.

## Context

These are the core ML pipelines — a client uploads images, the reconstructor builds a 3D map via pycolmap, and the localizer matches query images against stored maps using LightGlue. Testing these end-to-end requires GPU access and significant test data.

## Key files

- `docker/reconstructor/` — pycolmap-based 3D reconstruction
- `docker/localizer/` — LightGlue feature matching + RANSAC
- `docker/localizer/tests/test_build_metrics.py` — existing localizer test (requires PyTorch)

## Approach considerations

- These tests fundamentally need a GPU. They cannot run on standard GitHub Actions runners.
- Options: self-hosted GPU runner, GameCI Cloud Runner (supports GKE with GPU), or a separate CI system for GPU tests
- Test data: need a small, canonical dataset of images + expected reconstruction/localization results
- May need to accept that these tests run less frequently (nightly, or on-demand) rather than on every push
- Consider a "golden output" / regression test approach: run the pipeline once, store expected outputs, compare future runs

## Depends on

T5 (test patterns), GPU infrastructure (not a ticket).

## Done when

**Verifiable now (no special infra):**
- Test scaffolding exists
- Static analysis passes

**Requires GPU (verify manually later):**
- Golden output comparison passes
