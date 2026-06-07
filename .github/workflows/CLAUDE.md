# Workflow Conventions

## CI/release workflow separation

CI (build/test) and release (publish/tag) are separate workflows:

- **`placeframe-ci.yml`**: Triggers on `push: [dev]` and `pull_request: [dev]`. Contains: preflight, unity (calls `unity-build.yml`), build-docker, build-zed, publish-compose, ensure-release-pr. The `ensure-release-pr` job is gated on all builds passing and only runs on dev push.
- **`unity-build.yml`**: Reusable `workflow_call` workflow holding the Unity jobs (matrix, activate-license, build-unity). Designed for cross-repo consumption — other repos call it pinned to a ref with `secrets: inherit`; placeframe-ci calls it via local path so every PR exercises the shared file. It must stay self-contained: no relative composite-action references (those resolve against the *caller's* checkout), no repo-specific values. Editor container images are matrix-emitted, derived from each project's `ProjectVersion.txt`. The caller's `unity` job is deliberately ungated — Unity builds run parallel to preflight for faster PR feedback; release gating is enforced by `ensure-release-pr`'s `needs` instead.
- **`placeframe-release.yml`**: Triggers on `push: [main]`. Reuses CI artifacts by looking up the successful CI run for the same SHA via `gh api`. Uses `cancel-in-progress: false` — never abort a release mid-publish.
- All workflow logic lives in Python scripts invoked via `uv run` — no inline shell conditionals or loops (per repo-root convention).
