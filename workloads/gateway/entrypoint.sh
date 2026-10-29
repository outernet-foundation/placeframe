#!/bin/sh
set -eu

# Caddy always serves cleartext HTTP on :8443 with h2c enabled. TLS is either
# terminated upstream by a tunnel relay (ngrok) or absent entirely (LAN /
# air-gap, where cleartext on the local network is accepted to avoid the
# cert-distribution overhead of an internal CA on every Unity client). h2c is
# required so gRPC arriving over the relay's cleartext upstream connection
# negotiates HTTP/2.
#
# X-Forwarded-Proto / X-Forwarded-Port are parsed from PUBLIC_URL and exported
# as FORWARDED_PROTO / FORWARDED_PORT for the auth snippets to read via
# caddy's {$VAR} placeholder. Keycloak depends on this for redirect-URI
# matching when its KC_HOSTNAME embeds the public scheme.
#
# Auth composition is by file presence: the edge that runs an OIDC provider
# mounts /etc/caddy/snippets/{site,loki}/*.conf, an anonymous edge mounts
# nothing. caddy logs a warning on a no-match import glob, so each import is
# emitted only when its directory holds at least one snippet.

scheme="${PUBLIC_URL%%://*}"
rest="${PUBLIC_URL#*://}"
hostport="${rest%%/*}"
case "$hostport" in
    *:*) port="${hostport##*:}" ;;
    *)   if [ "$scheme" = "https" ]; then port=443; else port=80; fi ;;
esac

export FORWARDED_PROTO="$scheme"
export FORWARDED_PORT="$port"

site_imports=""
if ls /etc/caddy/snippets/site/*.conf >/dev/null 2>&1; then
    site_imports="    import /etc/caddy/snippets/site/*.conf"
fi
loki_imports=""
if ls /etc/caddy/snippets/loki/*.conf >/dev/null 2>&1; then
    loki_imports="        import /etc/caddy/snippets/loki/*.conf
"
fi

cat > /etc/caddy/Caddyfile <<EOF
{
    debug
    servers :8443 {
        protocols h1 h2c
    }
}

http://:8443 {
${site_imports}
    # Grafana
    handle /grafana/* {
        reverse_proxy grafana:3000
    }

    # Loki (log ingestion from Unity clients; anonymous clients push logs
    # unauthenticated, only the forward_auth gate is snippet-borne)
    handle /loki/* {
${loki_imports}        reverse_proxy loki:3100
    }

    # API Service
    handle {
        reverse_proxy api:8000
    }
}
EOF

exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
