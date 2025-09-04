#!/usr/bin/env bash

cat > /etc/caddy/Caddyfile <<EOF
:9000 {
    reverse_proxy minio:9000 {
        # The tailnet beacon rewrote the Host header to the tailnet MagicDNS address so 
        # that traffic can flow over the tailnet. Now we must set it back to the original 
        # host so that MinIO’s presigned URLs (which include the hostname in their signature) 
        # still validate correctly.
        header_up Host ${DEVICE_NAME}-minio.${DOMAIN}
    }
}
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