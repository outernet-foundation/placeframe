#!/usr/bin/env bash
set -euo pipefail

# Required env vars:
: "${GH_OWNER?}"       # e.g. "myOrg"
: "${GH_REPO?}"        # e.g. "myOrg/myRepo"
: "${RUNNER_LABELS?}"  # e.g. "self-hosted,vpc"
: "${RUNNER_WORKDIR:_work}"

# 1) Fetch a fresh registration token from our sidecar
echo "🔑  Fetching registration token for ${GH_REPO} via token-proxy…"
REG_TOKEN=$(curl -fsSL \
  "http://localhost:8080/register?repo=${GH_REPO}" \
  | jq -r .token)

if [[ -z "$REG_TOKEN" ]]; then
  echo "❌  Failed to get registration token"
  exit 1
fi

# 2) Configure the runner (unattended)
echo "⚙️  Configuring GitHub Actions runner…"
./config.sh --unattended \
  --url "https://github.com/${GH_REPO}" \
  --token "${REG_TOKEN}" \
  --labels "${RUNNER_LABELS}" \
  --work "${RUNNER_WORKDIR}"

# 3) Cleanup handler (deregister on shutdown)
cleanup() {
  echo "🗑️  Deregistering runner…"
  ./config.sh remove --unattended --token "${REG_TOKEN}"
}
trap cleanup EXIT

# 4) Launch the runner loop
echo "🚀  Starting runner…"
exec ./run.sh
