# 1. Declare the build arguments at the top
ARG GOLANG_IMAGE
ARG ALPINE_IMAGE

# --- build stage ---
# 2. Append the digest variable from images.lock. The ref carries no tag:
#    without the lock the build fails instead of floating to :latest.
FROM ${GOLANG_IMAGE} AS build
ARG PGS_VERSION=v1.0.2
RUN apk add --no-cache git \
    && go install github.com/stripe/pg-schema-diff/cmd/pg-schema-diff@${PGS_VERSION}

# --- runtime stage ---
# 3. Do the same for the runtime base
FROM ${ALPINE_IMAGE}
RUN apk add --no-cache ca-certificates bash
COPY --from=build /go/bin/pg-schema-diff /usr/local/bin/pg-schema-diff

# Add the entrypoint script
WORKDIR /app
COPY workloads/database-migrator/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
COPY database/ /app/database/

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]