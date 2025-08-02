FROM debian:bookworm-slim

# Copy and make entrypoint executable
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Ensure entrypoint script is in Unix format
RUN apt-get update \
 && apt-get install -y dos2unix \
 && dos2unix /usr/local/bin/entrypoint.sh

 # Set the entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]