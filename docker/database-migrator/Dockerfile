# --- build stage ---
FROM golang:1.22-alpine AS build
ARG PGS_VERSION=v1.0.2
RUN apk add --no-cache git \
    && go install github.com/stripe/pg-schema-diff/cmd/pg-schema-diff@${PGS_VERSION}

# --- runtime stage ---
FROM alpine:3.20
RUN apk add --no-cache ca-certificates bash
COPY --from=build /go/bin/pg-schema-diff /usr/local/bin/pg-schema-diff

# Add the entrypoint script
WORKDIR /app
COPY docker/database-migrator/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
