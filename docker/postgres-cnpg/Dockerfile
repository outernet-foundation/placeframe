# CloudNativePG operand image with PostGIS marked "trusted".
# CNPG runs its own instance manager, so the placeframe entrypoint-wrapper.sh cannot
# be used to trust PostGIS at runtime. Instead we mark the extension trusted in the
# image itself, so the non-superuser placeframe_owner can CREATE EXTENSION postgis in
# the temporary shadow databases pg-schema-diff creates during migration.
FROM ghcr.io/cloudnative-pg/postgis@sha256:8e05fbc908ffbdb34aaaf594ea8d108450266f686500fc6e6d78dd007f32c568

USER root
RUN for control in /usr/share/postgresql/14/extension/postgis*.control; do \
        grep -q 'trusted' "$control" || echo 'trusted = true' >> "$control"; \
    done
USER 26
