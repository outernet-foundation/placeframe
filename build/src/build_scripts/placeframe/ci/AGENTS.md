# CI Scripts Conventions

## CI commit-free invariant

CI and release workflows must not create commits on any branch. This ensures dev→main merges are always true fast-forwards. The tag ledger, path-diff change detection, and ephemeral version patching that implement this for publishing live in the external [`release-devkit`](https://github.com/outernet-foundation/release-devkit) repo (see its `AGENTS.md`); what remains local:

- **Built Docker images**: Tagged with `tree-<sha>` where the SHA is a `git write-tree` hash of all files visible per `.dockerignore` (which uses allowlist format). Per-service `${*_SHA}` variables in compose files are injected from `compute_service_shas` at bring-up/generation time, never written to a file. `workloads/images.lock` holds one `NAME=path:tag@sha256:…` pin per `workloads/images.yml` `x-base-images` declaration — never built-image digests.
