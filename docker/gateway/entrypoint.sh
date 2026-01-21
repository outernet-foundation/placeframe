#!/bin/sh
set -eu

cat > /etc/caddy/Caddyfile <<EOF
:8080 {
    redir /auth /auth/ 308

    respond /internal/* 403

    handle_path /auth/* {
        reverse_proxy keycloak:8080 {
            header_up X-Forwarded-Proto https
            header_up X-Forwarded-Port 443
            header_up X-Forwarded-Host {host}
        }
    }

    handle {
        reverse_proxy api:8000 {
            header_up X-Forwarded-Proto https
            header_up X-Forwarded-Port 443
            header_up X-Forwarded-Host {host}
        }
    }
}
EOF

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile