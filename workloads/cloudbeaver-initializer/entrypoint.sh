#!/usr/bin/env bash
set -euo pipefail

: "${POSTGRES_HOST}"
: "${POSTGRES_ADMIN_USER}"
: "${POSTGRES_ADMIN_PASSWORD}"
: "${CB_ADMIN_NAME}"
: "${CB_ADMIN_PASSWORD}"
: "${CLOUDBEAVER_DB_SCHEMA:=cloudbeaver}"

WORKSPACE="/opt/cloudbeaver/workspace"
DATA_DIR="${WORKSPACE}/.data"
DS_DIR="${WORKSPACE}/GlobalConfiguration/.dbeaver"
CONF_DIR="${WORKSPACE}/conf"

MARKER="${DATA_DIR}/.provision.hash"
RUNTIME_CONF="${DATA_DIR}/.cloudbeaver.runtime.conf"
INITIAL_DATA_CONF="${CONF_DIR}/initial-data.conf"
DATA_SOURCES_FILE="${DS_DIR}/data-sources.json"

INITIAL_DATA_JSON=$(cat <<EOF
{
  "adminName": "${CB_ADMIN_NAME}",
  "adminPassword": "${CB_ADMIN_PASSWORD}",
  "teams": [
    {
      "subjectId": "admin",
      "teamName": "Admin",
      "description": "Administrative access. Has total and full authority.",
      "permissions": ["admin"]
    },
    {
      "subjectId": "user",
      "teamName": "User",
      "description": "Standard user",
      "permissions": []
    }
  ]
}
EOF
)

DATA_SOURCES_JSON=$(cat <<EOF
{
  "folders": {},
  "connections": {
    "postgres": {
      "provider": "postgresql",
      "driver": "postgres-jdbc",
      "name": "postgres",
      "save-password": true,
      "configuration": {
        "host": "${POSTGRES_HOST}",
        "port": 5432,
        "database": "postgres",
        "user": "${POSTGRES_ADMIN_USER}",
        "password": "${POSTGRES_ADMIN_PASSWORD}",
        "url": "jdbc:postgresql://${POSTGRES_HOST}:5432/postgres"
      }
    }
  }
}
EOF
)

CLOUDBEAVER_RUNTIME_CONF_JSON=$(cat <<EOF
{
  "server": {
    "serverName": "CloudBeaver",
    "database": {
      "driver": "postgres-jdbc",
      "url": "jdbc:postgresql://${POSTGRES_HOST}:5432/postgres",
      "schema": "${CLOUDBEAVER_DB_SCHEMA}",
      "user": "${POSTGRES_ADMIN_USER}",
      "password": "${POSTGRES_ADMIN_PASSWORD}",
      "initialDataConfiguration": "${INITIAL_DATA_CONF}"
    }
  }
}
EOF
)

# Compute idempotence hash over all configuration files
NEW_HASH="$(printf '%s%s%s' \
  "${INITIAL_DATA_JSON}" \
  "${DATA_SOURCES_JSON}" \
  "${CLOUDBEAVER_RUNTIME_CONF_JSON}" \
  | sha256sum | awk '{print $1}')"

CURRENT_HASH="$(cat "${MARKER}" 2>/dev/null || true)"

if [[ "${NEW_HASH}" != "${CURRENT_HASH}" ]]; then
  echo "Configuration changed (or first run)"

  # Ensure directories exist
  mkdir -p "${DATA_DIR}" "${DS_DIR}" "${CONF_DIR}"

  # Drop CloudBeaver's server schema to keep the service stateless
  echo "Dropping CloudBeaver schema (if it exists)"
  export PGPASSWORD="${POSTGRES_ADMIN_PASSWORD}"
  psql -h "${POSTGRES_HOST}" -p 5432 -U "${POSTGRES_ADMIN_USER}" -d postgres \
    -v ON_ERROR_STOP=1 \
    -c "DROP SCHEMA IF EXISTS ${CLOUDBEAVER_DB_SCHEMA} CASCADE;"

  # Write configuration files
  echo "Writing configuration files"
  printf '%s\n' "${INITIAL_DATA_JSON}" > "${INITIAL_DATA_CONF}"
  printf '%s\n' "${DATA_SOURCES_JSON}" > "${DATA_SOURCES_FILE}"
  printf '%s\n' "${CLOUDBEAVER_RUNTIME_CONF_JSON}" > "${RUNTIME_CONF}"

  # Record new hash
  printf '%s\n' "${NEW_HASH}" > "${MARKER}"
else
  echo "No configuration changes detected"
fi

  echo "Initialization complete"
