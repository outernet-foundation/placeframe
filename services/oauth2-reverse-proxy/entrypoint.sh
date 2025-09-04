#!/usr/bin/env bash

cat > /etc/caddy/Caddyfile <<EOF
:4181 {
	# Forward the original request properties so oauth2-proxy can build absolute rd
	reverse_proxy ${UPSTREAM} {
		header_up X-Forwarded-Proto {scheme}
		header_up X-Forwarded-Host  {host}
		header_up X-Forwarded-Port  {server_port}
		header_up X-Forwarded-For   {remote}
		header_up X-Forwarded-Uri   {uri}

		# Force oauth2-proxy reverse-proxy path (Host != X-Forwarded-Host)
        # https://github.com/oauth2-proxy/oauth2-proxy/issues/1607
		header_up Host oauth2-proxy.internal

		transport http {
			versions h1
		}
	}

	# (Optional hardening)
	encode zstd gzip
}

EOF

echo "Starting Oauth2 reverse proxy with Caddy..."

# Start Caddy
exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile