#!/usr/bin/env bash

cat > /etc/caddy/Caddyfile <<EOF
:9001 {
    reverse_proxy minio:9001 {
        # Skip the MinIO console same-origin check by just removing the Origin header
        header_up -Origin
    }
}
EOF

echo "Starting MinIO reverse proxy with Caddy..."

# Start Caddy
exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile