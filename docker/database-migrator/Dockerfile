# 1. Declare the build arguments at the top
ARG GOLANG_DIGEST
ARG ALPINE_DIGEST

# --- build stage ---
# 2. Append the digest variable to the base image tag.
#    If locked: golang:1.22-alpine@sha256:abcdef...
#    If unlocked: golang:1.22-alpine
FROM golang:1.22-alpine${GOLANG_DIGEST} AS build
ARG PGS_VERSION=v1.0.2
RUN apk add --no-cache git \
    && go install github.com/stripe/pg-schema-diff/cmd/pg-schema-diff@${PGS_VERSION}

# --- runtime stage ---
# 3. Do the same for the runtime base
FROM alpine:3.20${ALPINE_DIGEST}
RUN apk add --no-cache ca-certificates bash
COPY --from=build /go/bin/pg-schema-diff /usr/local/bin/pg-schema-diff

# Add the entrypoint script
WORKDIR /app
COPY docker/database-migrator/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]