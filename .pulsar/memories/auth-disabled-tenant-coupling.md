---
updated: 2026-06-09
---

# Auth-disabled mode couples identity to tenant, so each device gets its own tenant and can't see another device's maps

## Goal

In auth-disabled mode, every device should resolve to the **same shared tenant** so that a localization map created on one phone is visible to another. Today they don't: each device's per-install anonymous id becomes a distinct user, each user gets its own auto-created personal tenant, and row-level security then hides each tenant's maps from every other device. Symptom observed live: the Samsung (which created the one existing map "SouthSideSeaport plaza") can see it; the Pixel cannot. This blocks the core cross-device relocalization use case (localize on phone B against a map captured by phone A).

## State

- No code changes made for this issue. Diagnosis only — the user invoked `/memorize` right after the recommendation, before any fix.
- Live DB state on 2026-06-09 (dev stack), confirming the bug end-to-end:
  - One map: `localization_maps.id = be918f75-7c9d-4f2b-9570-8c147a67c762`, name "SouthSideSeaport plaza", `active=t`, `tenant_id = d86afb42-198e-4e4d-911a-d7c98b9b2a1b`, `reconstruction_id = b3beb065-b3dc-43b6-a732-5a72e925a007`.
  - Two `auth.users`: `1c056640-…` (Samsung, created 16:38) and `f09a1d10-…` (Pixel, created 17:10).
  - Two `auth.tenants`: `d86afb42-…` (Samsung's personal) and `9b3be307-…` (Pixel's personal).
  - `auth.memberships`: each user is `owner` of its own tenant with `is_personal=t`. The map lives under Samsung's personal tenant `d86afb42`, so RLS filters it out for the Pixel.
- The two phones are distinguishable in logs only via the `capture-tool` stream's `deviceName` JSON field ("Emanuel's S23 FE" = Samsung, "Pixel 9"); backend `api`/`localizer`/`reconstructor` logs (OTel shape) carry no device identifier, IP, or user-agent, so backend logs cannot currently be attributed to a device.

## Decisions

- **Root cause is tenant *resolution*, not identity.** Keep per-device identity; stop letting identity dictate the tenant. Do **not** drop the anonymous-id logic.
- The confirmed chain:
  1. `docker/api/src/auth.py` (~lines 50-52): in disabled mode, `sub` = `x-anonymous-identity` header (each phone sends its own per-install UUID), with a dead `or "anonymous"` fallback.
  2. `docker/api/src/database.py:64-74`: `user_id = sub`; JIT-inserts a `User(id=user_id)` row and sets only `app.user_id` via `set_config("app.user_id", user_id, True)` (line 74). It **never sets `app.tenant_id`**.
  3. `database/10_users.sql` trigger: every new user row auto-creates a fresh personal tenant + owner membership.
  4. `current_tenant()` in `database/01_functions.sql:19-27`: `COALESCE(app.tenant_id, <user's personal-tenant membership>)`. With `app.tenant_id` unset, it falls through to the caller's personal tenant.
  5. `database/22_localization_maps.sql:52-53`: RLS `USING (tenant_id = current_tenant())`.
- So in disabled mode tenant is a pure function of `sub` (1:1 by construction). Decoupling them is the whole task.
- **Recommended structural fix** (reuse the existing `app.tenant_id` override branch of the `COALESCE`, which exists for the worker/service path):
  - Seed one well-known shared tenant (a constant UUID) via a migration so the `auth.tenants` FK is satisfied.
  - In `get_session`, when `auth_mode == "disabled"`, also `set_config("app.tenant_id", <shared tenant>, True)` alongside `app.user_id`. `current_tenant()` then returns the shared tenant for every anonymous device, while `app.user_id` stays per-device for ownership/attribution/audit.
  - Keep JIT user creation (identity preserved). The per-user personal tenant the trigger still mints just goes unused in disabled mode — harmless.
  - No membership row needed in the shared tenant: RLS checks `tenant_id = current_tenant()`, not membership.
- **Rejected option "always anonymous" (collapse all devices to one `sub`):** strictly worse — throws away per-device identity the user wants, and still needs a fixed anonymous UUID (the string literal won't insert), so it touches the same code anyway. Pin the tenant, keep the identity.
- **Latent bug to fix in passing:** the `or "anonymous"` fallback in `auth.py` can never have worked. `auth.users.id` is a `uuid` PK and `current_tenant()` casts `app.user_id::uuid`; a request without the header → `sub="anonymous"` → invalid-uuid insert/cast → 500. It only works because phones always send a UUID. Delete the string literal as part of the fix.

## Open questions

- What constant UUID to use for the shared anonymous tenant (any well-known value; pick one and document it in the migration).

## Key files

- `docker/api/src/auth.py` — disabled-mode branch (~50-52) that sets `sub` from `x-anonymous-identity`; drop the dead `or "anonymous"`.
- `docker/api/src/database.py` — `get_session` (56+); line 74 sets `app.user_id`. Add the `app.tenant_id` `set_config` here for disabled mode.
- `database/01_functions.sql` — `current_tenant()` (lines 11-30); the `app.tenant_id` COALESCE branch (line 20) is the override hook to use.
- `database/10_users.sql` — trigger that auto-creates a personal tenant + owner membership per new user.
- `database/22_localization_maps.sql` — RLS policy `tenant_id = current_tenant()` (lines 52-53).
- `database/12_tenants.sql` — `auth.tenants` table the seed migration must satisfy.

## Pending threads

- Implement the fix as two distinct steps so the code change can be reviewed independently of the data migration:
  1. **Code/schema:** seed migration for the shared tenant + `database.py` `set_config("app.tenant_id", …)` in disabled mode + delete the dead `"anonymous"` fallback.
  2. **Data migration (dev only):** re-point the existing map's rows from Samsung's personal tenant `d86afb42` to the new shared tenant so both phones can localize against it. Tenant-scoped tables to update: `localization_maps`, `reconstructions`, `capture_sessions`, `localization_map_camera_positions`. Enumerate exact rows before touching anything.
