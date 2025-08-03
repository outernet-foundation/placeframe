#!/usr/bin/env bash
set -euo pipefail

# Required env vars
: "${TS_AUTHKEY?}"
: "${CADDYFILE?}"

# Start tailscale daemon with more verbose logging
echo "Starting tailscaled..."
tailscaled \
  --state=/var/lib/tailscale/tailscaled.state \
  --socket=/run/tailscale/tailscaled.sock \
  --tun=userspace-networking \
  --verbose=2 \
  >/var/log/tailscaled.log 2>&1 &

# Wait for daemon to be ready
echo "Waiting for tailscaled to start..."
DAEMON_READY=false
for i in {1..30}; do
    if [[ -S /run/tailscale/tailscaled.sock ]] && \
       tailscale --socket=/run/tailscale/tailscaled.sock version >/dev/null 2>&1; then
        echo "tailscaled is ready"
        DAEMON_READY=true
        break
    fi
    echo "Waiting for tailscaled... ($i/30)"
    sleep 1
done

if [[ "$DAEMON_READY" != "true" ]]; then
    echo "ERROR: tailscaled failed to start"
    cat /var/log/tailscaled.log || true
    exit 1
fi

# Test network connectivity first
echo "Testing network connectivity..."
if ! curl -s -m 5 https://controlplane.tailscale.com >/dev/null; then
    echo "WARNING: Cannot reach Tailscale control plane"
fi

# Now connect with longer timeout and more debugging
echo "Connecting to Tailscale..."
if ! tailscale --socket=/run/tailscale/tailscaled.sock up \
    --authkey="${TS_AUTHKEY}" \
    --hostname=beacon \
    --accept-dns=false \
    --timeout=60s; then
    echo "ERROR: Failed to connect to Tailscale"
    echo "=== Tailscaled log (last 100 lines) ==="
    tail -100 /var/log/tailscaled.log || true
    echo "=== End log ==="
    
    # Check Tailscale status for more info
    echo "=== Tailscale status ==="
    tailscale --socket=/run/tailscale/tailscaled.sock status 2>&1 || true
    echo "=== End status ==="
    
    exit 1
fi

# Verify connection
echo "Verifying Tailscale connection..."
tailscale --socket=/run/tailscale/tailscaled.sock status

echo "Tailscale connected successfully"

# Start Caddy
echo "${CADDYFILE}" > /etc/caddy/Caddyfile
exec caddy run --config /etc/caddy/Caddyfile