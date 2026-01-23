#!/bin/sh
set -eu

cat > /etc/caddy/Caddyfile <<EOF
{
    debug
    
    # Enable h2c (Cleartext HTTP/2) on port 8080
    servers :8080 {
        protocols h1 h2c
    }
}

# Unified Listener (Port 8080)
# - Serves Ngrok via h2c
# - Serves Localhost via HTTP/1.1 or h2c
# - NO TLS / NO CERTIFICATES REQUIRED
:8080 {
    # gRPC Service
    @grpc {
        header Content-Type application/grpc*
    }
    handle @grpc {
        reverse_proxy state-sync:5000 {
            transport http {
                versions h2c 2
            }
            flush_interval -1
        }
    }

    # Auth Service
    handle_path /auth/* {
        reverse_proxy keycloak:8080 {
            header_up X-Forwarded-Proto https
            header_up X-Forwarded-Port 443
            header_up X-Forwarded-Host {host}
        }
    }

    # API Service
    handle {
        reverse_proxy api:8000
    }
}
EOF

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile