FROM caddy:2.8.4-alpine

# Install Tailscale and tools
RUN apk add --no-cache tailscale bash curl ca-certificates dos2unix \
 && mkdir -p /var/lib/tailscale /run/tailscale

# Entrypoint
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN dos2unix /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
