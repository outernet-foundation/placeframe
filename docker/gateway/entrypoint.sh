#!/bin/sh
set -eu

# 1. Extract the hostname (remove the port) from PUBLIC_DOMAIN
#    Input: "localhost:58080" -> Output: "localhost"
DOMAIN_NAME=${PUBLIC_DOMAIN%:*}

# 2. Generate Caddyfile with shell variables injected
cat > /etc/caddy/Caddyfile <<EOF
{
    debug
    # Global option: Allow Cleartext HTTP/2 (h2c) on port 8080 for Ngrok
    servers :8080 {
        protocols h1 h2c
    }
}

(backend_routes) {
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
            # Shell expands this to "58080" (or whatever you set)
            header_up X-Forwarded-Port ${PUBLIC_PORT} 
        }
    }

    # API Service
    handle {
        reverse_proxy api:8000
    }
}

# Listener A: Tunnel Mode (Ngrok) - Explicitly HTTP
http://:8080 {
    import backend_routes
}

# Listener B: Local Mode
# We explicitly list the domain so Caddy generates the correct cert.
# e.g., "localhost:8443"
${DOMAIN_NAME}:8443 {
    tls internal
    import backend_routes
}
EOF

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile