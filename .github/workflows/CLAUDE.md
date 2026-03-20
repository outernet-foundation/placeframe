# Workflow Conventions

## CI/release workflow separation

CI (build/test) and release (publish/tag) are separate workflows:

- **`ci.yml`**: Triggers on `push: [dev]` and `pull_request: [main, dev]`. Contains: preflight, activate-license, matrix, build-docker, build-unity, ensure-release-pr. The `ensure-release-pr` job is gated on all builds passing and only runs on dev push.
- **`release.yml`**: Triggers on `push: [main]`. Reuses CI artifacts by looking up the successful CI run for the same SHA via `gh api`. Uses `cancel-in-progress: false` — never abort a release mid-publish.
- All workflow logic lives in Python scripts invoked via `uv run` — no inline shell conditionals or loops (per repo-root convention).
