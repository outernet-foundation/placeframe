# Placeframe Unity package hardcodes `placeframe-dev` Keycloak realm

**Severity**: medium — blocks any non-dev deployment of the Placeframe Unity package without editing the package source.

**Location**: `packages/unity/Placeframe/Assets/Package/Core/Runtime/VisualPositioningSystem.cs:126` — `Login` builds `authTokenUrl` as `$"{apiUrl}/auth/realms/placeframe-dev/protocol/openid-connect/token"`.

**Symptom**: An operator standing up a production / staging Placeframe stack with any realm name other than `placeframe-dev` cannot authenticate from a Unity client using this package without forking it. The OAuth `client_id` is parameterised through `authAudience` on `Initialize`, but the realm is not — the asymmetry suggests an oversight, not a deliberate single-realm contract.

**Mechanism**: The realm path segment is a literal in `Login`. No `Initialize`-time parameter, no `appsettings`-style lookup, no environment-driven default.

**Fix sketch**: Either (a) add a `realm` parameter to `Login` (or `Initialize`) and thread it into the token URL, or (b) accept the full `authTokenUrl` from the caller. Default to `placeframe` (not `-dev`) once renamed, with the dev stack overriding to `placeframe-dev`. Coordinate the rename with `docker/keycloak/` realm configuration so a single realm name doesn't permanently outlive the "-dev" semantics.

**Verification**: Stand up a stack with a realm named `placeframe-prod`, configure a client to use that realm, log in. Assert authentication succeeds without editing the Unity package.
