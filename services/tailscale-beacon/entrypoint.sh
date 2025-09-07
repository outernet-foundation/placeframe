#!/usr/bin/env bash
set -euo pipefail

# Required env vars
: "${TS_AUTHKEY}"
: "${SERVICES}"
: "${DOMAIN}"
: "${TAILNET}"

# Start tailscale daemon with userspace networking (we can't load kernel modules in fargate containers)
# and a SOCKS5 proxy for outbound connections (can't use http proxy because we need websocket support)
echo "Starting tailscaled..."
tailscaled \
  --state=/var/lib/tailscale/tailscaled.state \
  --socket=/run/tailscale/tailscaled.sock \
  --tun=userspace-networking \
  --socks5-server=127.0.0.1:1055 \
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

# Check if daemon started successfully
if [[ "$DAEMON_READY" != "true" ]]; then
    echo "ERROR: tailscaled failed to start"
    cat /var/log/tailscaled.log || true
    exit 1
fi

# Test Tailscale control plane connectivity
echo "Testing Tailscale control plane connectivity..."
if ! curl -s -m 5 https://controlplane.tailscale.com >/dev/null; then
    echo "WARNING: Cannot reach Tailscale control plane"
fi

# Connect to Tailscale (disabling DNS because we want to use our VPC's DNS)
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

# Escape domain for regex
ESCAPED_DOMAIN=${DOMAIN//./\\.}

# Parse SERVICES entries: name:port[:rewrite]
# Default (no third field) means "norewrite" (preserve branded Host; e.g., for MinIO SigV4)
REWRITE_SVCS=()
NOREWRITE_SVCS=()
PORT_MAP_REWRITE=""
PORT_MAP_NOREWRITE=""

for spec in $SERVICES; do
    IFS=: read -r svc port mode <<< "$spec"
    mode="${mode:-norewrite}"
    if [[ -z "$svc" || -z "$port" ]]; then
        echo "ERROR: invalid SERVICES entry '$spec' (expected name:port[:requires_host_rewrite])" >&2
        exit 1
    fi
    if [[ "$mode" == "rewrite" ]]; then
        REWRITE_SVCS+=("$svc")
        PORT_MAP_REWRITE+="            $svc $port"$'\n'
    else
        NOREWRITE_SVCS+=("$svc")
        PORT_MAP_NOREWRITE+="            $svc $port"$'\n'
    fi
done

join_regex() { local IFS='|'; echo "$*"; }

REWRITE_REGEX="$(join_regex "${REWRITE_SVCS[@]}")"
NOREWRITE_REGEX="$(join_regex "${NOREWRITE_SVCS[@]}")"

# Generate Caddyfile
cat > /etc/caddy/Caddyfile <<EOF
:80 {
    respond /health 200

    # Match <device>-<service>.<DOMAIN> for services that PRESERVE Host
    @norewrite header_regexp norewrite Host ^([^.]+?)-(${NOREWRITE_REGEX})\.${ESCAPED_DOMAIN}\$
    handle @norewrite {
        # Map service -> port
        map {http.regexp.norewrite.2} {up_port} {
            ${PORT_MAP_NOREWRITE}            
            default 0
        }
        # Proxy to <device>.<TAILNET>.ts.net:<port>
        reverse_proxy {http.regexp.norewrite.1}.${TAILNET}.ts.net:{up_port} {
            # NOTE: Tailnet reachability comes from the SOCKS5 dial below, not Host.
            # We preserve the branded Host for services that require it (e.g., MinIO SigV4).
            header_up Host {host}
            transport http {
                forward_proxy_url socks5://127.0.0.1:1055
            }
        }
    }

    # Match <device>-<service>.<DOMAIN> for services that REQUIRE Host rewrite
    @rewrite header_regexp rewrite Host ^([^.]+?)-(${REWRITE_REGEX})\.${ESCAPED_DOMAIN}\$
    handle @rewrite {
        # Map service -> port
        map {http.regexp.rewrite.2} {up_port} {
            ${PORT_MAP_REWRITE}            
            default 0
        }
        # Proxy to <device>.<TAILNET>.ts.net:<port>
        reverse_proxy {http.regexp.rewrite.1}.${TAILNET}.ts.net:{up_port} {
            # Set Host to the tailnet authority so upstream vhosts/redirects/CSRF checks behave.
            header_up Host {upstream_hostport}
            transport http {
                forward_proxy_url socks5://127.0.0.1:1055
            }
        }
    }

    respond 404
}
EOF

echo "Generated Caddyfile:"
cat /etc/caddy/Caddyfile

# Format Caddyfile for readability
caddy fmt --overwrite /etc/caddy/Caddyfile

# Output the generated Caddyfile for debugging
echo "Generated Caddyfile:"
cat /etc/caddy/Caddyfile

# Start Caddy
echo "Starting Caddy with generated Caddyfile"
exec caddy run --config /etc/caddy/Caddyfile
