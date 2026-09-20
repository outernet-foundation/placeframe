# CI Scripts Conventions

## CI commit-free invariant

CI and release workflows must not create commits on any branch. This ensures dev→main merges are always true fast-forwards. The tag ledger, path-diff change detection, and ephemeral Unity `package.json` version patching that implement this for publishing live in the external [`pubpkg`](https://github.com/outernet-foundation/pubpkg) repo (see its `AGENTS.md`); what remains local:

- **Built Docker images**: Tagged with `tree-<sha>` where the SHA is a `git write-tree` hash of all files visible per `.dockerignore` (which uses allowlist format). Single `${CONTEXT_SHA:?err}` variable in compose files. `.env.lock` contains only base/third-party digests, never built-image digests.
