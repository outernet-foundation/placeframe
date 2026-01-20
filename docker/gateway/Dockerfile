ARG CADDY_DIGEST

FROM docker.io/library/caddy${CADDY_DIGEST}

# Copy the entrypoint and make it executable
COPY --chmod=0755 docker/gateway/entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]