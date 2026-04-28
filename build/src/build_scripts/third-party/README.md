# Third-party vendored files

## dotnet-install.sh

- **Source**: https://dot.net/v1/dotnet-install.sh
- **Upstream repo**: https://github.com/dotnet/install-scripts
- **License**: MIT (see header in script)
- **Vendored**: 2026-03-16
- **Why**: The `actions/setup-dotnet` GitHub Action bundles this script locally to avoid downloading it at runtime. We vendor it for the same reason — downloading it via curl inside CI containers is unreliable (timeouts).
