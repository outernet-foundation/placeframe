# CI

Build pipeline, linting, testing infrastructure, and continuous integration.

## npm OIDC trusted publishing (npmjs.org)

Packages under the `org.outernet` scope are published to npmjs.org using OIDC trusted publishing — no long-lived NPM_TOKEN needed.

**First publish of a new package:**

npm does not support configuring OIDC for packages that don't exist yet (unlike PyPI's "pending publisher" feature). The package must exist on npmjs.org before you can enable trusted publishing in its settings. Workaround:

1. Publish the first version locally: `npm publish --access public` from the package directory (requires being logged in to npm with an account that has publish access to the `org.outernet` scope)
2. Go to npmjs.org → Packages → the new package → Settings → Trusted publishing
3. Add the GitHub repo (`outernet-foundation/placeframe`) and workflow filename (e.g. `build-cesium-native.yml`)
4. Subsequent publishes from CI use OIDC automatically

**Prerelease versions** (e.g. `1.15.3-linux.1`): npm requires `--tag latest` (or another explicit tag) when publishing prerelease versions. Without it, publish fails with "You must specify a tag using --tag".

**Node version**: OIDC trusted publishing requires npm >=11.5.1 (ships with Node 24+). Do NOT use `setup-node`'s `registry-url` parameter — it writes a token placeholder `.npmrc` that blocks OIDC.

## ORAS cache ordering constraint

Caches stored via ORAS/GHCR that extract to paths under the clone target directory (e.g. `/tmp/cesium-build/cesium-unity-samples/...`) MUST be restored AFTER the clone phase, not before. The tar extraction creates the parent directory tree, which causes `git clone` to fail with "destination path already exists and is not an empty directory." This has bitten us twice (Library cache, then vcpkg cache). The fix is always the same: move the restore step to after clone and before the phase that needs the cached artifacts.
