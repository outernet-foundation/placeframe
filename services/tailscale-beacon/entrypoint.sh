#!/usr/bin/env bash
set -euo pipefail

# Required env vars (no defaults)
: "${TS_AUTHKEY:?TS_AUTHKEY must be set (injected as an ECS task secret)}"
: "${TAILNET_NAME:?TAILNET_NAME must be set (your tailnet name)}"
: "${CADDYFILE:?CADDYFILE must be set (text of the Caddyfile)}"

# Start tailscaled daemon
nohup tailscaled \
  --state=/var/lib/tailscale/tailscaled.state \
  --socket=/run/tailscale/tailscaled.sock \
  --tun=userspace-networking \
  >/var/log/tailscaled.log 2>&1 &

# Start tailscale client and wait for it to connect
tailscale --socket=/run/tailscale/tailscaled.sock up \
  --authkey="${TS_AUTHKEY}" \
  --hostname="${TS_HOSTNAME}" \
  --accept-dns=true \
  --timeout=30s

# Start Caddy
echo "${CADDYFILE}" > /etc/caddy/Caddyfile
exec caddy run --config /etc/caddy/Caddyfile
