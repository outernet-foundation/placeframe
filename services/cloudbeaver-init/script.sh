#!/bin/sh
set -e

CONFIG_DIR="/opt/cloudbeaver/workspace/GlobalConfiguration/.dbeaver"
mkdir -p "$CONFIG_DIR"

cat > "$CONFIG_DIR/data-sources.json" << EOF
{
  "folders": {},
  "connections": {
    "plerion": {
      "provider": "postgresql",
      "driver": "postgres-jdbc",
      "name": "Plerion",
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

echo "CloudBeaver configuration initialized."