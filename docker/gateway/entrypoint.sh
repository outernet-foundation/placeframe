#!/bin/sh
set -eu

# Extract the hostname (strip any :port) from PUBLIC_DOMAIN.
DOMAIN_NAME=${PUBLIC_DOMAIN%:*}

# GATEWAY_TLS_MODE controls how Caddy handles TLS:
#   internal — Caddy terminates HTTPS itself using an internal CA. Used for
#              LAN / air-gapped deployments where clients hit Caddy directly.
#              The site listener is :8443 (HTTPS).
#   plain    — Caddy serves plain HTTP, TLS is terminated upstream by the
#              tunnel relay (e.g. Localtonet's HTTP tunnel). The site listener
#              is :8443 (cleartext), and the relay rewrites the public URL to
#              HTTPS at the edge.
case "${GATEWAY_TLS_MODE}" in
    internal)
        SITE_ADDRESS="${DOMAIN_NAME}:8443"
        TLS_DIRECTIVE="tls internal"
        ;;
    plain)
        SITE_ADDRESS="http://:8443"
        TLS_DIRECTIVE=""
        ;;
    *)
        echo "GATEWAY_TLS_MODE must be 'internal' or 'plain', got: ${GATEWAY_TLS_MODE}" >&2
        exit 1
        ;;
esac

cat > /etc/caddy/Caddyfile <<EOF
{
    debug
}

${SITE_ADDRESS} {
    ${TLS_DIRECTIVE}

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
            header_up X-Forwarded-Port ${PUBLIC_PORT}
        }
    }

    # Grafana
    handle /grafana/* {
        reverse_proxy grafana:3000
    }

    # Loki (log ingestion from Unity clients, authenticated via Keycloak)
    handle /loki/* {
        forward_auth keycloak:8080 {
            uri /realms/placeframe-dev/protocol/openid-connect/userinfo
        }
        reverse_proxy loki:3100
    }

    # CloudBeaver
    redir /cloudbeaver /cloudbeaver/
    handle /cloudbeaver/* {
        reverse_proxy cloudbeaver:8978
    }

    # LiveKit Token Issuer
    handle_path /livekit-token/* {
        reverse_proxy livekit-token:8000
    }

    # API Service
    handle {
        reverse_proxy api:8000
    }
}
EOF

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
