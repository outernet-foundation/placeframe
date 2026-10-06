#!/bin/sh
# Make PostGIS extensions trusted so non-superusers (placeframe_owner) can
# CREATE EXTENSION postgis in pg-schema-diff's temporary databases.
for ctl in /usr/local/share/postgresql/extension/postgis*.control; do
    if ! grep -q 'trusted' "$ctl" 2>/dev/null; then
        echo 'trusted = true' >> "$ctl"
    fi
done

exec docker-entrypoint.sh postgres "$@"
