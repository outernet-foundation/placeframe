FROM docker.io/library/caddy:2.8.4-alpine

RUN apk add --no-cache bash dos2unix

# Copy the entrypoint and make it executable
COPY --chmod=0755 entrypoint.sh /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]