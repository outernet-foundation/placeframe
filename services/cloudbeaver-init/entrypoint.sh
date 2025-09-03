#!/usr/bin/env bash
set -euo pipefail

# --- 1) Require all env vars up front ---
: "${POSTGRES_HOST}"
: "${POSTGRES_DB}"
: "${POSTGRES_USER}"
: "${POSTGRES_PASSWORD}"
: "${CB_ADMIN_NAME}"
: "${CB_ADMIN_PASSWORD}"
: "${CLOUDBEAVER_DB_SCHEMA}"

# --- 2) Define workspace paths on EFS ---
WORKSPACE="/opt/cloudbeaver/workspace"
RUNTIME="$WORKSPACE/.data/.cloudbeaver.runtime.conf"
MARKER="$WORKSPACE/.data/.admin.seed"
CONFIG_DIR="$WORKSPACE/GlobalConfiguration/.dbeaver"

mkdir -p "$CONFIG_DIR" "$WORKSPACE/.data"

# --- 3) Write out your JDBC connection JSON ---
cat > "$CONFIG_DIR/data-sources.json" <<EOF
{
  "folders": {},
  "connections": {
    "plerion": {
      "provider": "postgresql",
      "driver": "postgres-jdbc",
      "name": "Plerion",
      "project": "GlobalConfiguration",
      "save-password": true,
      "configuration": {
        "host": "${POSTGRES_HOST}",
        "port": "5432",
        "database": "${POSTGRES_DB}",
        "user": "${POSTGRES_USER}",
        "password": "${POSTGRES_PASSWORD}"
      }
    }
  }
}
EOF

echo "📄 data-sources.json written."

# --- 4) Idempotent admin‐seed logic ---
HASH="$(printf '%s:%s' "$CB_ADMIN_NAME" "$CB_ADMIN_PASSWORD" | sha256sum | awk '{print $1}')"
CURRENT="$(cat "$MARKER" 2>/dev/null || true)"

if [[ "$HASH" != "$CURRENT" ]]; then
  echo "🔄 Admin credentials changed (or first run); FULL reset of CloudBeaver metadata..."

  export PGPASSWORD="${POSTGRES_PASSWORD}"

  # Drop CloudBeaver schema if present
  psql -h "${POSTGRES_HOST}" -p 5432 -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
       -v ON_ERROR_STOP=1 \
       -c "DROP SCHEMA IF EXISTS ${CLOUDBEAVER_DB_SCHEMA} CASCADE;"

  # Wipe EFS runtime config
  rm -rf "${WORKSPACE}/.data" "${CONFIG_DIR}"
  mkdir -p "${CONFIG_DIR}" "${WORKSPACE}/.data"

  echo "$HASH" > "$MARKER"
else
  echo "✅ Admin credentials unchanged; no reset needed."
fi

echo "Init sidecar complete."
