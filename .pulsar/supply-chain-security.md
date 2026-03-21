# Supply chain security — discussion notes

## The problem

Any Python dependency can do anything at runtime: filesystem, network, subprocess. There's no capability system. If a service imports a library, that library has full access. This creates two risks:

1. **Internal boundary violations** — e.g. the API service importing our subprocess wrapper (`bash.py`) when it should never shell out. The ruff S403/S603 rules can't see through wrapper indirection.
2. **External supply chain attacks** — a compromised or malicious PyPI package in our dependency tree.

## What we're doing now

- **deptry** verifies imports match declared dependencies (catches accidental transitive imports)
- **uv.lock** includes hashes (build-time integrity)
- **Package-split plan**: extract `bash.py` into its own package so only `build` and `scripts` can depend on it, enforced structurally via deptry (see details below)

## What we need

**CI-level gate requiring manual approval for any changes to pyproject.toml dependencies.** Specifically:

- Any PR that modifies a `[project.dependencies]` or `[project.optional-dependencies]` section in any pyproject.toml should require explicit human review before merge.
- This is not about automated scanning (though that's valuable too) — it's about ensuring a human decides "yes, this service should be allowed to depend on this package."
- Could be implemented as a GitHub required reviewer rule triggered by path changes, or a CI check that flags dependency changes and blocks merge until approved.

## Package-split plan for subprocess boundary

`bash.py` (in `common`) is the project's sole sanctioned subprocess wrapper. It suppresses ruff S404/S603 because subprocess calls are its entire purpose. But this creates a blind spot: any service that imports `bash.py` can shell out without ruff noticing, because S603 only flags literal `subprocess.run` calls, not calls through a wrapper. This is the same limitation as any library that wraps subprocess (paramiko, fabric, etc.).

**The fix is structural:** extract `bash.py` into its own package (e.g. `common-subprocess`) and only declare it as a dependency in projects that legitimately need to shell out (`build`, `scripts`). If `docker/api` or `docker/localizer` ever imports it, `deptry-check` flags the undeclared dependency. This enforces the subprocess boundary at the package level rather than relying on a lint rule that can't see through wrappers.

Nothing stops someone from adding the dependency to a service's `pyproject.toml` to bypass this — which is where the CI-level dependency approval gate (above) closes the loop.

## Longer-term layers

| Layer | What | Tools |
|---|---|---|
| Dependency declaration | Imports match declared deps | deptry (have this) |
| Build integrity | Downloaded package matches published | uv.lock hashes (have this) |
| Vulnerability scanning | Known CVEs in dependency tree | pip-audit, osv-scanner |
| Dependency approval | Human reviews every new dependency | CI gate (need this) |
| Per-service allow/deny | "API cannot depend on subprocess wrapper" | Package-split + deptry, or custom CI check |
| Transitive auditing | Full SBOM of what's actually in each image | syft + grype |
| Runtime capabilities | Restrict what a dependency can do | Not possible in Python |
