FROM docker.io/library/caddy:2.8.4-alpine

# Install Tailscale and tools
RUN apk add --no-cache tailscale bash curl ca-certificates dos2unix \
    && mkdir -p /var/lib/tailscale /run/tailscale

# Copy the entrypoint and make it executable
COPY --chmod=0755 entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
