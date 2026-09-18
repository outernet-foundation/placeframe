# CI Scripts Conventions

## CI commit-free invariant

CI and release workflows must not create commits on any branch. This ensures dev→main merges are always true fast-forwards.

- **Version tracking**: Per-package git tags (`{package}-v{semver}`, e.g. `core-v1.0.3`, `release-v0.2.0`), not committed state files.
- **Change detection**: `git diff --quiet <last-tag> HEAD -- <path>`, not content hashing. Dependency cascading (`depends_on`) must still trigger dependents even if their own paths haven't changed.
- **Built Docker images**: Tagged with `tree-<sha>` where the SHA is a `git write-tree` hash of all files visible per `.dockerignore` (which uses allowlist format). Single `${CONTEXT_SHA:?err}` variable in compose files. `.env.lock` contains only base/third-party digests, never built-image digests.
- **Unity package.json versions**: Set to `0.0.0-local` permanently. Patched ephemerally during `npm publish`, then restored immediately — never committed.
