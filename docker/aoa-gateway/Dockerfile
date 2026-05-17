ARG CADDY_DIGEST

FROM docker.io/library/caddy${CADDY_DIGEST}

COPY docker/aoa-gateway/Caddyfile /etc/caddy/Caddyfile

CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
