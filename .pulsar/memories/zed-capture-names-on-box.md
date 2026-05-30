---
updated: 2026-05-29
---

# Persist ZED capture names on the box instead of on the phone

## Goal

ZED capture names are currently stored only on the phone (the AndroidMobile
Capture Tool), inside a `LocalCaptureNames.json` file. The ZED box itself
holds no record of what a capture was named. Reinstalling the Capture Tool
wipes the local file and every capture's user-chosen name with it. The user
just hit this failure mode in practice — renamed several captures, then
reinstalled, then the names were gone. The fix is to move the name's
source of truth onto the ZED box so it survives client reinstalls and is
visible to any future client.

## State

No code changed yet. The proposal was sketched out and the user asked for
it to be memorized as an initiative; implementation has not started. Open
across at least these files (paths verified to exist):

- `docker/zed-capture/src/routers/captures.py` — `/captures` endpoint
  (around line 52 returns the `ZedCapture` model). Needs a `name` field
  and a `PATCH /captures/{id}/name` route added.
- `apps/AndroidMobile/Assets/Scripts/Capture/CaptureController.cs` —
  `OnCaptureNameChanged` (around line 216) currently writes to
  `LocalCaptureNames.json`; needs to be rewritten to call the new PATCH
  route. The merge logic that overlays local names onto the server list
  (around line 288) collapses to `state.name.value = remote?.Name` once
  the server is authoritative.

## Decisions

- **Sidecar file on the box, not a manifest field.** Put the name in
  something like `~/captures/{uuid}/name.txt` rather than adding it to
  `manifest.json`. `manifest.json` is geometry/config and is rewritten by
  the recorder; bolting a mutable user-supplied string into that file
  conflates two different lifecycles. Sidecar keeps them separated.

- **Write-on-rename, not write-at-start.** Unnamed captures have no
  sidecar file on disk; `/captures` reports `name = None` for them.
  Simpler than writing an empty file at capture start. The UI already
  handles the "no name" case. (Counter-option considered: write-at-start
  with a default like the rig hostname — rejected as more files for no
  user-visible benefit.)

- **One-shot migration on first connect after the upgrade.** Every
  entry in the phone's existing `LocalCaptureNames.json` whose id matches
  a server capture gets PATCHed to the new endpoint, then the local
  file is deleted. Without this, anyone upgrading loses the names they
  already typed — i.e. the exact failure mode that prompted this
  initiative. Worth getting right; not optional.

- **Server is the single source of truth post-migration.** The
  `LocalCaptureNames.json` path and the `_localCaptureNames` dict can go
  away entirely after the migration step.

## Key files

- `docker/zed-capture/src/routers/captures.py` — `/captures` GET around
  line 52 returns `ZedCapture`. Add `name: str | None` and add a new
  `PATCH /captures/{id}/name` route here. Pydantic model bump means C#
  client regen.
- `apps/AndroidMobile/Assets/Scripts/Capture/CaptureController.cs` —
  `OnCaptureNameChanged` (~ line 216) is the call site to rewrite.
  Local-name merge logic (~ line 288) collapses to a single assignment
  once the server is authoritative.
- `LocalCaptureNames.json` (on the phone) — current home of the names,
  to be migrated then deleted.

## Pending threads

- Implement the sidecar read/write on the box side and surface `name`
  on `ZedCapture`.
- Add `PATCH /captures/{id}/name`.
- `uv run generate-clients` after the API change.
- Rewrite `OnCaptureNameChanged` to PATCH the server; remove the local
  dict and its persistence path.
- Add the one-shot migration that drains `LocalCaptureNames.json` into
  the server then deletes the local file.
- Verify on the user's existing setup (the one where this just hit)
  that names captured pre-migration survive the install.
