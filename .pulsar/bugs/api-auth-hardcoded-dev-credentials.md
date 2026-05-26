# `api_auth.py` hardcodes dev Keycloak credentials with no environment override

**Severity**: medium — rotating any credential breaks every script in `scripts/` simultaneously; couples dev workflow to a specific Keycloak realm config.

**Location**: `scripts/src/scripts/api_auth.py:35-47` (`_fetch_keycloak_token`).

**Symptom**: `client_id="placeframe-api"`, `username="user"`, `password="password"`, and realm `placeframe-dev` are baked into the source. There is no `os.environ.get(...)` fallback. Any rotation in Keycloak — renaming the realm, changing the dev user, adding a client secret — requires editing this file (and re-deploying every consumer) rather than a `.env` flip.

**Mechanism**: The values were inlined when the helper was first written and never parameterized. `_read_public_domain` already demonstrates the `.env`-reading pattern this function should follow.

**Fix sketch**: Read `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_DEV_USERNAME`, `KEYCLOAK_DEV_PASSWORD` from the repo `.env` (extending `_read_public_domain` into a generic `_read_env_var(name, default)` helper). Provide the current values as defaults so existing local stacks keep working without `.env` edits.

**Verification**: After fix, rotating the Keycloak dev password in `.env` + restarting Keycloak should leave `uv run fit-calibration --help` (and friends) authenticating successfully without source edits.
