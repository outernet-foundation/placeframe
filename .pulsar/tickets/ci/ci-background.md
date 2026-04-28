# CI/CD Background & Philosophy

Shared context for CI-related tickets (T1-T8). Read this before starting work on any of them.

## What we have today

- Single GitHub Actions workflow: `.github/workflows/build.yml`
- Triggers on push to `main`, builds Docker images for CUDA and ROCm via `docker buildx bake`, pushes to ghcr.io, opens a PR to update `.env.lock` with pinned image digests
- Build orchestration lives in `scripts/src/scripts/build.py` — real Python code, not inline YAML
- No linting, typechecking, or tests in CI yet
- No Unity client builds in CI yet
- No branch-based builds — only `main`

## Guiding principles

These emerged from research into how Google, Uber, Stripe, and others approach CI correctness:

1. **The pipeline is software.** Build logic lives in `scripts/src/scripts/`, not in YAML. CI workflow files should be thin wrappers that call `uv run <command>`. This is already the case and should stay that way.

2. **Keep `docker buildx bake` as the build engine.** Dagger, Bazel, and Nix were evaluated and rejected — Dagger is pre-1.0 with stability concerns, Bazel is wildly over-engineered for this scale, Nix has an extreme learning curve and fragile CUDA support, and Earthly is dead. `buildx bake` is the right tool.

3. **Local reproducibility over CI-specific tooling.** Rather than using `act` to simulate GitHub Actions locally (which adds ugly `if: ${{ !env.ACT }}` conditionals everywhere), invest in making the underlying scripts (`build.py`, etc.) testable and runnable locally. CI is just the trigger.

4. **Hermetic where it matters, pragmatic where it doesn't.** Full hermeticity (Bazel-style) is overkill. But the build scripts should produce deterministic outputs for given inputs, and the argument-assembly logic should be testable without running Docker.

5. **Vendor caution with GitHub Actions.** GitHub Actions is ubiquitous but Microsoft's recent moves toward paid plans are concerning. Mitigate by keeping all real logic in Python scripts that any CI system could call. The workflow YAML should be trivially portable to GitLab CI, Buildkite, etc.

## Research findings

- **Docker registry caching** (`type=registry` with `mode=max`) uses standard OCI manifests — a local Docker registry reproduces the same caching behavior as ghcr.io, so caching bugs can be debugged locally without `act`.
- **Pre-built base image strategy** is the standard approach for large ML layers — separate the PyTorch/CUDA base from application code so the multi-GB layers aren't rebuilt on every commit.
- **GameCI** remains the dominant open-source option for Unity CI. Its v3 roadmap aims for CI-agnostic CLI but that's still in development. Key pain points: license activation, 25GB disk limit on GitHub runners, no GPU in CI.
- **GameCI licensing trick**: All Linux Docker images hardcode `machine-id` `576562626572264761624c65526f7578` in `/etc/machine-id`, so Unity's license server sees all containers as one machine. This is why parallel builds work with a single serial (1 of 2 activation slots). **Windows containers do NOT have this** — each gets a unique machine hash, consuming a separate slot. See `.pulsar/research/unity-ci-licensing.md` for full analysis.
- **Snapshot testing** of build script outputs (using `docker buildx bake --print`) is a practical way to test build orchestration logic without running actual builds.
- **npm publishing from git-cloned directories**: npm uses `.gitignore` as its ignore list when no `.npmignore` exists. If the upstream repo gitignores build artifacts (like `Plugins/`), `npm publish` will silently drop files you copied into the directory — even though they're on disk. Always add a `.npmignore` when publishing a package from a git clone that has its own `.gitignore`.
