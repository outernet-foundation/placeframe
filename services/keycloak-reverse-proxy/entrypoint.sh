#!/bin/sh
cat > /etc/caddy/Caddyfile <<EOF
:8080 {
    reverse_proxy keycloak:8080 {
        # Restore the public host so Keycloak sees the branded domain
        header_up Host ${DEVICE_NAME}-keycloak.${DOMAIN}
        header_up X-Forwarded-Host ${DEVICE_NAME}-keycloak.${DOMAIN}

        # Force the original external scheme; inner proxy would otherwise set "http"
        header_up X-Forwarded-Proto https
        header_up X-Forwarded-Port 443
    }
}
EOF

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
