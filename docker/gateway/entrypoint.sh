#!/bin/sh
set -eu

# Caddy always serves cleartext HTTP on :8443 with h2c enabled. TLS is either
# terminated upstream by a tunnel relay (ngrok) or absent entirely (LAN /
# air-gap, where cleartext on the local network is accepted to avoid the
# cert-distribution overhead of an internal CA on every Unity client). h2c is
# required so gRPC arriving over the relay's cleartext upstream connection
# negotiates HTTP/2.
#
# X-Forwarded-Proto / X-Forwarded-Port are parsed from PUBLIC_URL so the
# upstream sees the scheme and port the client actually connected to, not the
# gateway's internal 8443 bind. Keycloak depends on this for redirect-URI
# matching when its KC_HOSTNAME embeds the public scheme.
#
# AUTH_MODE composition: the /auth/* reverse proxy and the /loki/* forward_auth
# gate are only emitted when AUTH_MODE=keycloak. In AUTH_MODE=disabled the
# Keycloak container isn't running (compose profile gating), so those
# directives would either fail at boot or never resolve their upstream.

AUTH_MODE="${AUTH_MODE:-keycloak}"

scheme="${PUBLIC_URL%%://*}"
rest="${PUBLIC_URL#*://}"
hostport="${rest%%/*}"
case "$hostport" in
    *:*) port="${hostport##*:}" ;;
    *)   if [ "$scheme" = "https" ]; then port=443; else port=80; fi ;;
esac

if [ "$AUTH_MODE" = "keycloak" ]; then
    auth_handler="
    handle_path /auth/* {
        reverse_proxy keycloak:8080 {
            header_up X-Forwarded-Proto ${scheme}
            header_up X-Forwarded-Port ${port}
        }
    }
"
    loki_forward_auth="        forward_auth keycloak:8080 {
            uri /realms/placeframe-dev/protocol/openid-connect/userinfo
        }
"
else
    auth_handler=""
    loki_forward_auth=""
fi

cat > /etc/caddy/Caddyfile <<EOF
{
    debug
    servers :8443 {
        protocols h1 h2c
    }
}

http://:8443 {
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
${auth_handler}
    # Grafana
    handle /grafana/* {
        reverse_proxy grafana:3000
    }

    # Loki (log ingestion from Unity clients)
    handle /loki/* {
${loki_forward_auth}        reverse_proxy loki:3100
    }

    # CloudBeaver
    redir /cloudbeaver /cloudbeaver/
    handle /cloudbeaver/* {
        reverse_proxy cloudbeaver:8978
    }

    # API Service
    handle {
        reverse_proxy api:8000
    }
}
EOF

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
