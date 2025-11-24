#!/usr/bin/env bash
set -euo pipefail

# Required env:
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, SCHEMA_DIR
# Optional:
#   ALLOWED_HAZARDS (comma-separated)
#   EXTRA_PGOPTIONS (defaults to "-c check_function_bodies=off")

: "${DB_HOST:?set DB_HOST}"
: "${DB_PORT:=5432}"
: "${DB_NAME:?set DB_NAME}"
: "${DB_USER:?set DB_USER}"
: "${DB_PASSWORD:?set DB_PASSWORD}"
: "${DATABASE_SCHEMA_DIR:?set DATABASE_SCHEMA_DIR}"
: "${EXTRA_PGOPTIONS:="-c check_function_bodies=off"}"
: "${ALLOWED_HAZARDS:=""}"

# Percent-encode a minimal set for the options query param
encode_opts() {
  # encode spaces and '='; '&' and '%' are uncommon here but keep simple
  printf %s "$1" \
    | sed -e 's/%/%25/g' -e 's/ /%20/g' -e 's/=/%3D/g' -e 's/&/%26/g'
}

ENC_OPTS="$(encode_opts "$EXTRA_PGOPTIONS")"
OWNER_DSN="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?options=${ENC_OPTS}"

args=(apply --from-dsn "$OWNER_DSN" --to-dir "/app/${DATABASE_SCHEMA_DIR}" --skip-confirm-prompt)

if [[ -n "${ALLOWED_HAZARDS}" ]]; then
  args+=(--allow-hazards "$ALLOWED_HAZARDS")
fi

echo "pg-schema-diff ${args[*]}"
exec pg-schema-diff "${args[@]}"
