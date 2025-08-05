# Dockerfile
FROM ghcr.io/actions/actions-runner:latest

# Allow root to install our tiny deps
USER root

# Install curl + jq for the GitHub API call
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl jq \
    && rm -rf /var/lib/apt/lists/*

# Copy in your custom entrypoint
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Ensure entrypoint script is in Unix format
RUN apt-get update \
    && apt-get install -y dos2unix \
    && dos2unix /usr/local/bin/entrypoint.sh

# Switch back to the runner user
USER runner


ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
