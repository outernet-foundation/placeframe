FROM debian:bookworm-slim

RUN set -eux; \
    # Add Caddy repo
    echo "deb [trusted=yes] https://dl.cloudsmith.io/public/caddy/stable/debian/bookworm any-version main" \
      > /etc/apt/sources.list.d/caddy-stable.list; \
    # Install prerequisites and Caddy
    apt-get update; \
    apt-get install -y --no-install-recommends \
      apt-transport-https \
      ca-certificates \
      curl \
      gnupg \
      caddy; \
    # Install Tailscale
    curl -fsSL https://tailscale.com/install.sh | sh; \
    # Cleanup and prepare dirs
    rm -rf /var/lib/apt/lists/*; \
    mkdir -p /var/lib/tailscale /run/tailscale

# Copy and make entrypoint executable
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Ensure entrypoint script is in Unix format
RUN apt-get update \
     && apt-get install -y dos2unix \
     && dos2unix /usr/local/bin/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]